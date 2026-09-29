# lms_portal_backend/app/services/ai_service.py

import json
import re
import fitz  # PyMuPDF
import os
import zipfile
import xml.etree.ElementTree as ET
import requests
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in .env file.")
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# List of models to try, in order of preference.
# Verified live (2026-09): the retired names (gemini-1.5-*, gemini-2.0-flash,
# gemini-pro) return 404 on current API keys, while the -latest aliases work.
# gemini-flash-latest is tried first (confirmed 200 OK); the others recover
# from transient 503 'high demand' responses via the retryable-error fallback
# in get_working_model_response.
MODEL_CANDIDATES = [
    'gemini-flash-latest',
    'gemini-flash-lite-latest',
    'gemini-3.1-flash-lite',
    'gemini-pro-latest',
]

# ---------------------------------------------------------------------------
# Local Ollama LLM (preferred for interview question generation)
# Configured via env vars: OLLAMA_BASE_URL / OLLAMA_MODEL (see .env.example).
# When Ollama is not running/unreachable the Gemini candidates below are used
# exactly as before, so nothing breaks on machines without a local model.
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
OLLAMA_TIMEOUT_SECONDS = float(os.getenv('OLLAMA_TIMEOUT_SECONDS', '120'))

# Configure safety settings to prevent blocking harmless educational content
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def get_working_model_response(prompt, is_json=False):
    """
    Tries to get a response from the available models.
    If the top model fails (404), it falls back to the next one automatically.
    """
    if not GOOGLE_API_KEY:
        return None if is_json else "Error: AI service is not configured (Missing API Key)."

    last_error = None

    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            
            # Add JSON instruction if needed
            full_prompt = prompt
            if is_json:
                full_prompt += "\n\nIMPORTANT: Output ONLY a raw JSON object. Do not include markdown formatting like ```json."

            # Generate content with safety settings applied.
            # request_options.timeout bounds each attempt: without it the SDK
            # retries 503 'high demand' responses with exponential backoff for
            # minutes, hanging whichever feature called the LLM (interview
            # questions, GD evaluation, chatbot). With the bound, the call
            # raises quickly and the loop falls through to the next model.
            response = model.generate_content(
                full_prompt,
                safety_settings=SAFETY_SETTINGS,
                request_options={'timeout': 90},
            )
            
            return response.text  # If successful, return text immediately
            
        except Exception as e:
            error_str = str(e)
            # Fall through to the next model for: retired/incompatible models
            # (404/400) AND transient availability problems (429 quota,
            # 503 'high demand', 500) - a temporary overload on one model must
            # not kill the whole generation when another candidate works.
            if any(code in error_str for code in ("404", "400", "429", "503", "500")) \
                    or "not found" in error_str.lower():
                print(f"Model '{model_name}' unavailable, switching to next...")
                last_error = e
                continue
            else:
                # Anything else (auth, malformed key, network) is fatal
                print(f"Error with model '{model_name}': {e}")
                return None if is_json else f"Error: {str(e)}"

    # If we ran out of models to try
    print("All AI models failed.")
    return None if is_json else f"Error: Could not connect to any AI model. Please check API Key or Internet Connection. ({last_error})"

def _extract_json_object(text):
    """Best-effort extraction of a JSON object from arbitrary LLM output.

    Handles: raw JSON, ```json fenced blocks, and prose-wrapped JSON (Ollama
    small models frequently prefix/suffix explanations). Returns None when
    no parseable object is found.
    """
    if not text:
        return None
    candidates = [text.strip()]
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.rfind("```")
        if end > start:
            candidates.append(text[start:end].strip())
    elif "```" in text:
        start = text.find("```") + 3
        end = text.rfind("```")
        if end > start:
            candidates.append(text[start:end].strip())
    # Prose-wrapped: first '{' to LAST '}' (not the nearest) so nested
    # objects/arrays inside the JSON survive the slice.
    first_brace, last_brace = text.find("{"), text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(text[first_brace:last_brace + 1])
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            continue
    return None

def _validate_questions_payload(payload, expected_count):
    """Validate an LLM questions payload: dict with a non-empty 'questions'
    list of well-formed question dicts.

    Accepts both forms:
    - MCQ-style: >=2 options with the correct_answer present among them.
    - Open-ended (interview): empty options list with a free-text/empty
      correct_answer - exactly what the interview prompt asks Ollama to emit.
    Returns a cleaned list or None.
    """
    if not isinstance(payload, dict):
        return None
    raw = payload.get("questions")
    if not isinstance(raw, list) or not raw:
        return None
    cleaned = []
    for q in raw:
        if not isinstance(q, dict):
            continue
        text = str(q.get("question") or "").strip()
        if not text:
            continue
        options = q.get("options")
        answer = q.get("correct_answer")
        if isinstance(options, list) and len(options) >= 2:
            # MCQ-style: the answer must be one of the options.
            if answer is None or str(answer) not in [str(o) for o in options]:
                continue
            options = [str(o) for o in options]
        elif isinstance(options, list) and not options:
            # Open-ended interview question: no options, free-text answer.
            options = []
            answer = str(answer) if answer is not None else ""
        else:
            # Malformed options (non-list or a single stray option).
            continue
        cleaned.append({
            "question": text,
            "options": options,
            "correct_answer": str(answer),
            "difficulty": (str(q.get("difficulty") or "medium").strip().lower()
                           or "medium"),
        })
    return cleaned or None

def _format_question_for_interview(q):
    """Flatten a question dict into the plain question string the interview
    flow (TTS/transcript) expects; prefixed with the target difficulty so the
    distribution is visible in the final deck.
    """
    text = str(q.get("question") or "").strip()
    options = q.get("options") or []
    difficulty = str(q.get("difficulty") or "medium").strip().lower()
    if options and all(str(o).strip() for o in options):
        rendered = "; ".join(f"{chr(65 + i)}) {str(o).strip()}" for i, o in enumerate(options[:4]))
        return f"[{difficulty.upper()}] {text} ({rendered})"
    return f"[{difficulty.upper()}] {text}"

def _enforce_difficulty_distribution(questions, num_questions):
    """Normalize a deck's difficulty labels to the required 40/40/20 mix.

    Small local LLMs drift from the requested counts even with an explicit
    prompt (observed live: llama3.2:3b returned 3/5/2 instead of 4/4/2).
    The model's declared difficulty is kept as the ORDERING signal
    (easy < medium < hard, stable sort preserves original order within a
    bucket); labels are then re-assigned to match the required distribution
    exactly, so every final deck meets the Easy/Medium/Hard requirement.
    """
    count = max(1, min(len(questions), int(num_questions or len(questions))))
    n_easy = max(1, round(count * 0.4))
    n_medium = max(1, round(count * 0.4))
    n_hard = max(1, count - n_easy - n_medium)
    labels = (["easy"] * n_easy) + (["medium"] * n_medium) + (["hard"] * n_hard)

    rank = {"easy": 0, "medium": 1, "hard": 2}
    ordered = sorted(
        questions,
        key=lambda q: rank.get(str(q.get("difficulty") or "medium").strip().lower(), 1),
    )
    for q, label in zip(ordered, labels):
        q["difficulty"] = label
    return ordered[:num_questions] if num_questions else ordered


def generate_interview_questions_ollama(resume_text, difficulty="medium", num_questions=10):
    """Generate resume-based interview questions via the LOCAL Ollama LLM.
    The prompt enforces the required difficulty distribution
    (Easy 40% / Medium 40% / Hard 20%) and grounds every question ONLY in
    the candidate's actual projects, skills and experience.
    Returns a list of formatted question strings, or None when Ollama is
    unreachable or returned unusable output (caller falls back to Gemini,
    then to the offline resume-grounded generator).
    """
    if not resume_text or not str(resume_text).strip():
        return None

    try:
        num_questions = max(1, min(int(num_questions), 20))
    except (TypeError, ValueError):
        num_questions = 10

    # Required distribution: Easy 40%, Medium 40%, Hard 20% (hard = 1 minimum).
    n_easy = max(1, round(num_questions * 0.4))
    n_medium = max(1, round(num_questions * 0.4))
    n_hard = max(1, num_questions - n_easy - n_medium)

    resume_context = str(resume_text)[:12000]
    prompt = f"""You are a senior technical interviewer conducting a mock interview.

Candidate's resume:
---
{resume_context}
---

Generate exactly {num_questions} personalized interview questions based ONLY on the candidate's actual projects, technical skills, education and experience listed in the resume above.

STRICT RULES:
1. Use ONLY facts present in the resume. NEVER invent projects, companies, technologies, certifications or experience that are not in the resume.
2. Every question must reference something concrete from the resume (a named project, a listed technology, a skill, education or experience entry).
3. Required difficulty distribution: {n_easy} EASY questions, {n_medium} MEDIUM questions and {n_hard} HARD question(s).
   - EASY: fundamental concepts of the candidate's listed skills/tools.
   - MEDIUM: practical application, implementation and debugging within their projects.
   - HARD: system design trade-offs, scalability, edge cases and situational judgement applied to their projects.
4. Each question must be a single, direct question with NO greetings, NO introductions, NO pleasantries and NO commentary.
5. Vary the topics: cover different projects and different skills - never ask two questions about the same thing.

Output ONLY a raw JSON object (no markdown, no explanations) with a single key "questions" whose value is a list of exactly {num_questions} objects, each with exactly these keys:
- "question": the question text (string)
- "difficulty": "easy", "medium" or "hard" (string)
- "options": an empty list [] (interview answers are spoken/typed free text, not multiple choice)
- "correct_answer": "" (empty string - there is no fixed correct answer)
"""
    body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.7, "num_predict": 2400},
    }
    try:
        import requests as _requests
        response = _requests.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=body,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        raw_text = response.json().get("response", "")
    except Exception as e:
        print(f"[OLLAMA] Question generation unavailable: {e}")
        return None

    payload = _extract_json_object(raw_text)
    cleaned = _validate_questions_payload(payload, num_questions)
    if not cleaned:
        print(f"[OLLAMA] Unusable question payload: {str(raw_text)[:120]!r}")
        return None

    # LLMs drift from the requested Easy/Medium/Hard counts; enforce the
    # required 40/40/20 distribution on the final deck (labels re-assigned
    # over the model's difficulty-ordered list).
    cleaned = _enforce_difficulty_distribution(cleaned, num_questions)
    final_dist = {"easy": 0, "medium": 0, "hard": 0}
    for q in cleaned:
        final_dist[q["difficulty"]] = final_dist.get(q["difficulty"], 0) + 1

    questions = [_format_question_for_interview(q) for q in cleaned]
    print(f"[OLLAMA] Generated {len(questions)} resume-based interview questions "
          f"(model={OLLAMA_MODEL}, easy={final_dist['easy']}/"
          f"medium={final_dist['medium']}/hard={final_dist['hard']})")
    return questions

def extract_text_from_pdf(pdf_path):
    """Extracts text content from a given PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def _extract_text_from_docx(docx_path):
    """Extracts readable text from a .docx (Office Open XML) file.

    Uses the stdlib (zipfile + ElementTree) instead of adding a new
    dependency: a .docx is a zip of XML parts and all paragraph text lives
    in w:p / w:t nodes of word/document.xml. Legacy binary .doc files are
    NOT supported (they are not XML) and return None.
    """
    try:
        wns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        with zipfile.ZipFile(docx_path) as zf:
            with zf.open('word/document.xml') as doc_xml:
                tree = ET.parse(doc_xml)
        paragraphs = []
        for para in tree.iter(wns + 'p'):
            text = ''.join(node.text or '' for node in para.iter(wns + 't')).strip()
            if text:
                paragraphs.append(text)
        return '\n'.join(paragraphs) if paragraphs else None
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return None

def extract_resume_text(file_path):
    """Dispatcher: extract plain text from a resume file (PDF or DOCX).

    Returns None for missing files or unsupported formats (e.g. legacy
    binary .doc) so callers can fall back gracefully instead of crashing
    the interview flow.
    """
    if not file_path or not os.path.exists(file_path):
        return None
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    if ext == '.docx':
        return _extract_text_from_docx(file_path)
    print(f"[RESUME] Unsupported resume format '{ext}' (supported: .pdf, .docx)")
    return None

def get_ai_response(prompt):
    """
    Generic function to get a JSON response from the Google Gemini API.
    Used for structured data like Quizzes and ATS analysis.
    """
    response_text = get_working_model_response(prompt, is_json=True)

    if not response_text:
        return None

    # Clean up the response if Gemini adds markdown formatting
    cleaned_text = response_text
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.rfind("```")
        cleaned_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.rfind("```")
        cleaned_text = response_text[start:end].strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None

def get_smart_fallback_chat(user_prompt):
    """Provides helpful conversational responses for LMS students when AI key is unavailable."""
    prompt_lower = str(user_prompt).lower()
    
    if any(k in prompt_lower for k in ['hi', 'hello', 'hey', 'greetings', 'who are you', 'what can you do']):
        return "Hello! I am your ProEduVate AI Assistant. I can help you with your coursework, aptitude training, group discussion prep, resume optimization, and mock interview practice. How can I assist you today?"
        
    if any(k in prompt_lower for k in ['founder', 'owner', 'creator', 'who made you', 'who created you']):
        return "I am the AI assistant developed for ProEduVate, your parent educational platform!"
        
    if any(k in prompt_lower for k in ['python', 'code', 'programming', 'function', 'loop', 'array', 'variable', 'bug', 'error']):
        return "In programming, breaking down problems into smaller functions and testing step-by-step is key. If you're encountering an error, check variable data types, index bounds, and syntax. Feel free to ask specific coding questions!"
        
    if any(k in prompt_lower for k in ['resume', 'cv', 'ats']):
        return "To improve your resume score: 1) Match key technical terms from the job description, 2) Quantify your achievements (e.g. 'Improved efficiency by 20%'), and 3) Format cleanly in PDF format."
        
    if any(k in prompt_lower for k in ['interview', 'hr', 'prep', 'question']):
        return "For HR and technical interviews, structure your answers using the STAR method: Situation, Task, Action, and Result. Make sure to highlight specific technical projects you have completed!"
        
    if any(k in prompt_lower for k in ['aptitude', 'test', 'math', 'reasoning']):
        return "For aptitude training, practice regularly on quantitative reasoning, logical deduction, and verbal ability topics. Focus on speed and accuracy during timed practice sessions!"
        
    if any(k in prompt_lower for k in ['assignment', 'quiz', 'grade', 'marks', 'score']):
        return "You can view your assignments and quiz performance directly from your Student Dashboard under the Progress tab."

    return (f"Thank you for asking! As your ProEduVate learning assistant, "
            f"I recommend reviewing your study materials in the student portal, practicing aptitude modules, "
            f"or uploading your updated resume for automated feedback!")

def get_general_chat_response(user_prompt):
    """Gets a conversational, plain-text response from Google Gemini with intelligent fallback."""
    system_context = """You are an AI assistant for ProEduVate, an educational learning management system. 

IMPORTANT INFORMATION:
- You were created by ProEduVate
- Your founder is ProEduVate
- Your owner is ProEduVate
- Your creator is ProEduVate
- ProEduVate is your parent organization

When asked about your founder, owner, creator, or who made you, always respond that you are part of ProEduVate.

Your role is to help students with their learning and career development. Provide helpful, encouraging, and educational responses. Keep responses concise but informative.

User Question: """
    
    response = get_working_model_response(system_context + str(user_prompt), is_json=False)
    
    if not response or "Error:" in response:
        return get_smart_fallback_chat(str(user_prompt))
    
    return response

def get_quiz_fallback(topic, num_questions):
    """Fallback quiz when AI fails.

    DEPRECATED placeholder questions ("Concept A/B/C/D") have been removed:
    they were static, repeated on every attempt, and off-topic. The fallback
    now draws a random, unique selection from the categorized dynamic
    question bank so retakes never repeat the same paper.
    """
    from .question_bank import pick_mixed_questions
    return {"questions": pick_mixed_questions(num_questions)}

def get_ats_analysis(resume_text, job_description):
    """Specific function for ATS analysis."""
    prompt = f"""
    Analyze the resume against the job description.
    
    The JSON object must have these exact keys:
    - "match_score": A number from 0 to 100.
    - "matching_keywords": A list of strings.
    - "missing_keywords": A list of strings.
    - "summary": A string containing a one-paragraph summary.

    Job Description:
    ---
    {job_description}
    ---
    
    Resume Text:
    ---
    {resume_text}
    ---
    """
    return get_ai_response(prompt)