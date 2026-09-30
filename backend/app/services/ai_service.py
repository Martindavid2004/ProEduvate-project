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
    return ordered[:num_questions] if num_questions else ordered# ---------------------------------------------------------------------------
# Resume highlighting (projects + skills). Reads ONLY the resume text -
# nothing is ever invented. Shared by the Ollama prompt builder below and
# the offline fallback generator in interview_routes.py.
# ---------------------------------------------------------------------------
# Broad tech/skill lexicon (case-insensitive, word-boundary matched). Only
# terms ACTUALLY present in the resume are ever reported by
# extract_resume_highlights - the list being long costs nothing; inventing
# terms is what is forbidden.
_SKILLS_KEYWORDS = [
    # Languages
    'Java', 'Python', 'JavaScript', 'TypeScript', 'C', 'C++', 'C#', 'PHP',
    'Kotlin', 'Swift', 'Go', 'Rust', 'Ruby', 'R', 'MATLAB', 'Scala', 'Dart',
    # Web frameworks / libraries
    'React', 'Angular', 'Vue.js', 'Next.js', 'Node.js', 'Express.js', 'Flask',
    'Django', 'FastAPI', 'Spring', 'Spring Boot', 'Hibernate', 'Laravel',
    'Bootstrap', 'Tailwind CSS', 'jQuery', 'HTML', 'CSS', 'Sass', 'Redux',
    # Mobile
    'Android', 'Flutter', 'React Native', 'Ionic',
    # Data / ML / AI
    'Machine Learning', 'Deep Learning', 'Data Science', 'NLP', 'Computer Vision',
    'OpenCV', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas',
    'NumPy', 'Matplotlib', 'Seaborn', 'XGBoost', 'YOLO', 'Hugging Face',
    'LangChain', 'Generative AI', 'LLM',
    # Data stores / search
    'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'SQLite', 'Firebase', 'Redis',
    'Oracle', 'DynamoDB', 'Elasticsearch', 'Cassandra',
    # Cloud / DevOps / tools
    'AWS', 'Azure', 'Google Cloud', 'GCP', 'Docker', 'Kubernetes', 'Jenkins',
    'Git', 'GitHub', 'GitLab', 'CI/CD', 'Linux', 'Bash', 'Terraform', 'Ansible',
    'Nginx', 'Apache', 'Vercel', 'Netlify', 'Heroku', 'Render',
    # Architecture / practices
    'REST API', 'REST', 'GraphQL', 'WebSockets', 'Socket.io', 'Microservices',
    'OAuth', 'JWT', 'RabbitMQ', 'Kafka', 'Spark', 'Hadoop', 'ETL', 'Power BI',
    'Tableau', 'Blockchain', 'Solidity', 'Android Studio', 'VS Code', 'Figma',
    'Jira', 'Agile', 'Scrum', 'Selenium', 'Jest', 'Pytest', 'JUnit', 'Cypress',
    'Data Structures', 'Algorithms', 'OOP', 'Operating Systems', 'Networking',
    'Cyber Security', 'Cryptography', 'UI/UX',
]

# Project header formats matched (one project per line):
#   "MedVision AI - FastAPI, React, MongoDB"
#   "Crime Department Project | Python OpenCV MySQL"
#   "Smart Attendance System: Flask, OpenCV"
#   "- E-Commerce Platform (MERN stack)"      (bullet + parenthesised tech)
#   "* Library Management System using Java and MySQL"  ("using ..." tech)
_PROJECT_HEADER = re.compile(
    r'^\s*(?:[-*\u2022]+\s*)?'
    r'([A-Z][A-Za-z0-9 .&+_/]{2,60}?)'
    r'\s*(?:[\-\u2013\u2014:|]\s*|\.+\s*|\()'   # - | : ... ( separators
    r'(.+?)'                                      # tech string
    r'(?:\))?\s*$')

# "Project Name using X, Y and Z" (no separator before the tech list)
_PROJECT_USING = re.compile(
    r'^\s*(?:[-*\u2022]+\s*)?'
    r'([A-Z][A-Za-z0-9 .&+_/?]{2,60}?)'
    r'\s+using\s+(.+)$', re.IGNORECASE)

# Free-form tech words inside a project's tech string (catches stacks not in
# the curated lexicon, e.g. 'YOLOv8', 'Raspberry Pi', 'OpenCV').
_TECH_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+#./ _-]{1,30}")


def extract_resume_highlights(resume_text):
    """Extract skills and project names/tech-stacks actually present in the resume.

    Returns (found_skills, projects) where projects is a list of
    (project_name, tech_string). Every term returned is matched verbatim in
    the resume text - nothing is invented. Tech strings are NORMALISED to the
    curated lexicon when the resume spells them that way ("built with
    Python, OpenCV and a MySQL database" -> "Python, OpenCV, MySQL") so the
    LLM digest and offline questions cite the exact canonical tool names.
    """
    found_skills = []
    projects = []
    if not resume_text:
        return found_skills, projects

    _canon = {s.lower(): s for s in _SKILLS_KEYWORDS}

    for skill in _SKILLS_KEYWORDS:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            found_skills.append(skill)

    def _normalise_tech(tech_str):
        """Canonicalise a raw tech string against the lexicon, preserving
        first-appearance order and de-duplicating."""
        seen, out = set(), []
        # Split on list separators AND the glue word 'and' so "Flask, OpenCV
        # and SQLite" -> [Flask, OpenCV, SQLite].
        parts = re.split(r"[,;/]|\band\b", tech_str or '')
        for part in parts:
            for token in _TECH_TOKEN.findall(part):
                t = token.strip(' .,-')
                if not t or len(t) < 2:
                    continue
                key = t.lower()
                canon = _canon.get(key)
                if canon:
                    t = canon
                elif key not in seen and len(t) <= 30:
                    # Keep unknown-but-plausible tech tokens as-is (project
                    # specific hardware/models); drop boilerplate glue words.
                    if key in ('and', 'the', 'with', 'using', 'based', 'stack',
                               'built', 'developed', 'etc'):
                        continue
                elif canon is None:
                    continue
                if key not in seen:
                    seen.add(key)
                    out.append(t)
        return ', '.join(out[:6])

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()
        if not line or len(line) > 160:
            continue
        # Strip leading bullets so "- Crime Dept Project | Python" matches.
        stripped = re.sub(r'^[-*\u2022]+\s*', '', line)
        name = tech = None
        m = _PROJECT_HEADER.match(stripped)
        if m:
            name, tech = m.group(1).strip(), m.group(2).strip()
        else:
            mu = _PROJECT_USING.match(stripped)
            if mu:
                name, tech = mu.group(1).strip(), mu.group(2).strip()
        if not name:
            continue
        # Skip lines that look like section headers / contact info rather
        # than projects.
        if re.search(r'(education|experience|skills|certification|achievement'
                     r'|declaration|contact|profile|summary|objective|intern)',
                     name, re.IGNORECASE):
            continue
        if re.search(r'@(gmail|hotmail|yahoo|outlook)', name):
            continue
        tech = _normalise_tech(tech)
        # Date/period-only "tech" strings ("Summer 2025", "Jan 2024 - Present")
        # mark an EXPERIENCE line, not a project - drop it.
        if not tech or re.fullmatch(
                r'[\s\d,\-\u2013]*(summer|winter|fall|spring|mon|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|present)?[\s\d,\-\u2013]*',
                tech, re.IGNORECASE):
            continue
        projects.append((name, tech))
    return found_skills, projects[:10]


def build_resume_highlights_digest(resume_text, max_projects=6):
    """Compact bullet digest of the resume's projects/skills for the LLM prompt.

    Small local models follow a short, explicit extract far more reliably
    than a long raw resume, so the digest anchors their questions to the
    candidate's REAL projects and tech stack.
    """
    skills, projects = extract_resume_highlights(resume_text)
    lines = []
    if projects:
        lines.append('Projects found in the resume (name -> technologies):')
        for name, tech in projects[:max_projects]:
            lines.append(f'- {name} -> {tech}')
    if skills:
        lines.append('Skills/technologies listed in the resume: ' + ', '.join(skills))
    return '\n'.join(lines)


# Words that carry no resume-specific meaning when matching a generated
# question back to the resume text. Distinctive words (project names, tech
# terms, domain nouns) are what count as grounding evidence.
_GROUNDING_STOPWORDS = frozenset({
    'tell', 'about', 'your', 'yourself', 'what', 'when', 'where', 'which',
    'would', 'could', 'should', 'shall', 'there', 'here', 'have', 'has',
    'had', 'with', 'this', 'that', 'these', 'those', 'they', 'them', 'from',
    'into', 'onto', 'over', 'under', 'explain', 'describe', 'discuss',
    'experience', 'experiences', 'interview', 'candidate', 'question',
    'questions', 'answer', 'answers', 'example', 'instance', 'time', 'walk',
    'through', 'challenge', 'challenges', 'situation', 'strength',
    'strengths', 'weakness', 'weaknesses', 'future', 'years', 'role',
    'company', 'good', 'great', 'make', 'made', 'easy', 'medium', 'hard',
    'does', 'did', 'doing', 'will', 'can', 'and', 'the', 'for', 'you',
    'are', 'was', 'were', 'how', 'why', 'who', 'whom', 'not', 'but',
    'use', 'used', 'using', 'give', 'gave', 'some', 'any', 'also',
})


def _dedupe_questions(questions):
    """Remove near-duplicate questions (case/punctuation-insensitive)."""
    seen = set()
    out = []
    for q in questions or []:
        key = re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', str(q).lower())).strip()
        if key and key not in seen:
            seen.add(key)
            out.append(q)
    return out


def filter_ungrounded_questions(questions, resume_text):
    """STRICT resume grounding: drop questions that share NO vocabulary with
    the resume text.

    A question whose distinctive words (len >= 4, non-stopword) never appear
    in the resume is either generic/boilerplate ("Where do you see yourself
    in 5 years?") or references invented technology - both violate the
    resume-only requirement. Dropped questions are replaced by the caller's
    resume-grounded offline generator.
    """
    resume_lower = re.sub(r'\s+', ' ', str(resume_text or '')).lower()
    kept = []
    for q in questions or []:
        words = re.findall(r"[a-z0-9][a-z0-9+#.\-]{2,}", str(q).lower())
        grounded = any(
            len(w) >= 4 and w not in _GROUNDING_STOPWORDS
            and re.search(r'\b' + re.escape(w), resume_lower)
            for w in words
        )
        if grounded:
            kept.append(q)
        else:
            print(f"[OLLAMA] Grounding filter dropped non-resume question: "
                  f"{str(q)[:90]!r}")
    return kept


def generate_interview_questions_ollama(resume_text, difficulty="medium", num_questions=10,
                                        timeout_seconds=None):
    """Generate resume-based interview questions via the LOCAL Ollama LLM.

    The prompt enforces the required difficulty distribution
    (Easy 40% / Medium 40% / Hard 20%) and grounds every question ONLY in
    the candidate's actual projects, skills and experience. A post-generation
    grounding filter drops any question that shares no vocabulary with the
    resume, so generic or invented questions never reach the student.

    timeout_seconds: wall-clock cap for THIS call. When given it overrides
    OLLAMA_TIMEOUT_SECONDS and is always capped below the socket timeout so
    the caller's overall generation budget can actually be met (the request
    raises, the caller falls back to Gemini / the offline generator instead
    of the interview start hanging).

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
    highlights_digest = build_resume_highlights_digest(resume_context)
    digest_block = (
        "RESUME HIGHLIGHTS (verified extract - your questions MUST be built "
        "from these):\n" + highlights_digest + "\n\n"
    ) if highlights_digest else ""
    prompt = f"""You are a senior technical interviewer conducting a mock interview.

Candidate's resume:
---
{resume_context}
---

{digest_block}Generate exactly {num_questions} personalized interview questions based ONLY on the candidate's actual projects, technical skills, education and experience listed in the resume above.

STRICT RULES:
1. DO NOT ask generic or irrelevant questions (e.g. "tell me about yourself", "where do you see yourself in 5 years", strengths/weaknesses, hobbies). Every question must be one that ONLY this candidate could answer well from their resume.
2. Derive every question STRICTLY from the projects, their architecture, the tools and the tech skills mentioned in the resume. Name the specific project or technology in the question wording (e.g. ask about the candidate's actual named project and its stated tech stack, never about "a project you built" in the abstract).
3. Required difficulty distribution: {n_easy} EASY questions, {n_medium} MEDIUM questions and {n_hard} HARD question(s).
   - EASY: fundamental concepts of the candidate's listed skills/tools.
   - MEDIUM: practical application, implementation and debugging within their projects.
   - HARD: system design trade-offs, scalability, edge cases and situational judgement applied to their projects.
4. Use ONLY facts present in the resume. NEVER invent projects, companies, technologies, certifications or experience that are not in the resume. Reuse the EXACT project names and technology names from the resume in the question wording.
5. Each question must be a single, direct question with NO greetings, NO introductions, NO pleasantries and NO commentary.
6. Vary the topics: cover different projects and different skills - never ask two questions about the same thing.

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
        # Respect the caller's wall-clock budget: the request timeout is the
        # effective per-call deadline (min of env default and caller budget).
        effective_timeout = OLLAMA_TIMEOUT_SECONDS
        if timeout_seconds is not None:
            try:
                # Keep a 1s margin below the caller's budget so the client
                # socket raises (and we fall back) BEFORE the caller gives up.
                effective_timeout = max(2.0, min(float(timeout_seconds), 600.0) - 1.0)
            except (TypeError, ValueError):
                pass
        response = _requests.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=body,
            timeout=effective_timeout,
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

    # Deduplicate, then STRICTLY ground the deck: any question that shares no
    # vocabulary with the resume is generic or invented and is dropped here.
    # The caller tops the deck back up from its resume-grounded generator, so
    # the student only ever sees resume-tailored questions.
    questions = _dedupe_questions(
        [_format_question_for_interview(q) for q in cleaned])
    questions = filter_ungrounded_questions(questions, resume_context)

    if not questions:
        print("[OLLAMA] No resume-grounded questions survived the filter")
        return None

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