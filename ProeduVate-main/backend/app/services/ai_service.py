# lms_portal_backend/app/services/ai_service.py

import json
import fitz  # PyMuPDF
import os
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
MODEL_CANDIDATES = [
    'models/gemini-2.5-flash',
    'models/gemini-2.5-pro',
    'models/gemini-flash-latest',
    'models/gemini-pro-latest'
]

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

            # Generate content with safety settings applied
            response = model.generate_content(
                full_prompt, 
                safety_settings=SAFETY_SETTINGS
            )
            
            return response.text  # If successful, return text immediately
            
        except Exception as e:
            error_str = str(e)
            # Check for common "Not Found" or "400" errors which imply model incompatibility
            if "404" in error_str or "not found" in error_str.lower() or "400" in error_str:
                print(f"Model '{model_name}' unavailable, switching to next...")
                last_error = e
                continue
            else:
                # If it's a different error (like quota or auth), stop trying and report it
                print(f"Error with model '{model_name}': {e}")
                return None if is_json else f"Error: {str(e)}"

    # If we ran out of models to try
    print("All AI models failed.")
    return None if is_json else f"Error: Could not connect to any AI model. Please check API Key or Internet Connection. ({last_error})"

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

def get_general_chat_response(user_prompt):
    """Gets a conversational, plain-text response from Google Gemini."""
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
    
    response = get_working_model_response(system_context + user_prompt, is_json=False)
    
    # If AI service fails, provide a helpful fallback message
    if not response or "Error:" in response:
        return ("I'm currently experiencing connectivity issues with the AI service. "
                "This could be due to an invalid API key, network issues, or service unavailability. "
                "Please check your GOOGLE_API_KEY in the .env file or try again later. "
                "For immediate assistance, please contact your teacher or administrator.")
    
    return response

def get_quiz_fallback(topic, num_questions):
    """Fallback function to generate a simple quiz when AI fails."""
    sample_questions = [
        {"question": f"Which of the following is a key concept in {topic}?", "options": ["Concept A", "Concept B", "Concept C", "Concept D"], "correct_answer": "Concept A"},
        {"question": f"What is the main purpose of {topic}?", "options": ["Purpose A", "Purpose B", "Purpose C", "Purpose D"], "correct_answer": "Purpose B"},
        {"question": f"Which tool is commonly used for {topic}?", "options": ["Tool A", "Tool B", "Tool C", "Tool D"], "correct_answer": "Tool C"},
    ]
    return {"questions": sample_questions[:min(num_questions, len(sample_questions))]}

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