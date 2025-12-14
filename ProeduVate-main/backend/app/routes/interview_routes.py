# in interview_routes.py

from flask import Blueprint, jsonify, request, current_app
from ..database import users_collection
from bson import ObjectId
import os
# Import the service that communicates with the AI
from ..services.ai_service import extract_text_from_pdf, get_ats_analysis, get_ai_response

interview_bp = Blueprint('interview_bp', __name__, url_prefix='/api/interview')

# --- Enhanced HR-style Interview Questions ---
@interview_bp.route('/start', methods=['POST'])
def start_interview():
    """Generates realistic HR interview questions with personality, problem-solving, and skills assessment."""
    data = request.get_json()
    user_id = data.get('user_id')
    difficulty = data.get('difficulty', 'medium').lower()

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("resume_filename"):
        return jsonify({"error": "Resume not found. Please upload a resume first."}), 404

    resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user["resume_filename"])
    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text:
        return jsonify({"error": "Could not read resume file."}), 500

    # Craft a professional HR interviewer prompt
    prompt = f"""
    You are a friendly, professional HR interviewer conducting a real job interview. Your goal is to assess the candidate holistically - their personality, problem-solving abilities, technical skills, and cultural fit.

    IMPORTANT INTERVIEW STRUCTURE:
    1. START with a warm, conversational opening question (like "How has your day been so far?" or "Tell me a bit about yourself")
    2. Ask about their PERSONALITY and soft skills (teamwork, communication, handling pressure)
    3. Ask PROBLEM-SOLVING questions (how they handle challenges, conflicts, difficult situations)
    4. Ask SKILL-BASED questions related to their resume (about their experience, projects, technologies)
    5. Include behavioral questions (tell me about a time when...)
    6. Mix easy conversational questions with more thoughtful ones

    Based on the candidate's resume below, generate EXACTLY 10 interview questions that flow naturally like a real HR interview.

    Question Guidelines:
    - Question 1 MUST be a warm opening like "How has your day been?" or "How are you feeling today?" or "Tell me about yourself"
    - Include 2-3 personality/soft skills questions
    - Include 2-3 problem-solving/behavioral questions  
    - Include 3-4 skill/experience questions based on their resume
    - Make questions sound natural and conversational, not robotic
    - Be polite, warm, and encouraging in tone
    - Difficulty level: {difficulty}

    Return your response as a single, raw JSON object with one key: "questions", which holds a list of exactly 10 question strings in interview order.
    Do not include any other text or formatting - ONLY the JSON object.

    Candidate's Resume:
    ---
    {resume_text}
    ---
    """
    
    ai_response = get_ai_response(prompt)
    if not ai_response or "questions" not in ai_response:
        return jsonify({"error": "Failed to generate questions from AI model."}), 500
    
    # Ensure we have exactly 10 questions
    questions = ai_response.get("questions", [])
    if len(questions) < 10:
        # Add some generic HR questions if needed
        fallback_questions = [
            "How has your day been so far?",
            "What motivated you to apply for this position?",
            "How do you handle working under pressure?",
            "Can you tell me about a time you faced a challenge at work and how you overcame it?",
            "What are your greatest strengths?",
            "Where do you see yourself in 5 years?",
            "How do you approach learning new skills?",
            "Tell me about a time you worked in a team.",
            "What interests you most about this role?",
            "Do you have any questions for me?"
        ]
        questions.extend(fallback_questions[:10 - len(questions)])
    
    return jsonify({"questions": questions[:10]}), 200


# Enhanced HR-style evaluation
@interview_bp.route('/evaluate', methods=['POST'])
def evaluate_answers():
    """Evaluates the candidate like a real HR professional with constructive, supportive feedback."""
    data = request.get_json()
    user_id = data.get('user_id') or data.get('studentId')
    transcript = data.get('transcript')
    questions = data.get('questions', [])
    answers = data.get('answers', [])
    
    # If transcript is not provided but questions and answers are, build transcript
    if not transcript and questions and answers:
        transcript = []
        for i, (question, answer) in enumerate(zip(questions, answers)):
            transcript.append({
                'question': question,
                'answer': answer
            })

    if not transcript:
        return jsonify({"error": "No transcript provided."}), 400

    formatted_transcript = "\n".join([f"Question: {item['question']}\nAnswer: {item['answer']}\n---" for item in transcript])

    prompt = f"""
    You are a professional, empathetic HR interviewer providing feedback after completing an interview. 
    
    Your feedback should be:
    - Warm, encouraging, and professional
    - Constructive and specific
    - Balanced (highlighting both strengths and areas for growth)
    - Supportive of the candidate's development
    
    Evaluate the candidate on:
    - Communication skills and clarity
    - Problem-solving approach
    - Technical knowledge (if applicable)
    - Personality and cultural fit indicators
    - Professionalism and enthusiasm
    - Use of specific examples

    Return your response as a single, raw JSON object with these exact keys:
    - "score": An integer from 0 to 100 (be fair and encouraging)
    - "feedback": A warm, detailed paragraph (3-5 sentences) that sounds like a real HR professional speaking. Start with positive observations, then provide constructive suggestions for improvement.
    - "strengths": A list of 3-5 specific strengths you noticed (e.g., "Great communication skills", "Provided specific examples")
    - "mistakes": A list of 2-4 areas for improvement, phrased positively (e.g., "Consider elaborating more on your problem-solving process" instead of "You didn't explain well")

    Interview Transcript:
    ---
    {formatted_transcript}
    ---
    """
    
    ai_response = get_ai_response(prompt)
    if not ai_response:
        return jsonify({"error": "Failed to get evaluation from AI model."}), 500

    interview_score = ai_response.get("score")
    if interview_score is not None:
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"interviewScore": interview_score}}
        )

    return jsonify(ai_response), 200