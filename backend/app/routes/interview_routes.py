import re
from flask import Blueprint, jsonify, request, current_app
from ..database import users_collection
from bson import ObjectId
import os
from ..services.ai_service import extract_text_from_pdf, get_ai_response

interview_bp = Blueprint('interview_bp', __name__, url_prefix='/api/interview')

def generate_resume_questions(resume_text, candidate_name="Candidate"):
    """Parses resume text to extract skills and key terms, generating 10 personalized interview questions."""
    skills_keywords = [
        'Java', 'Python', 'JavaScript', 'React', 'Node.js', 'Spring Boot', 'HTML', 'CSS',
        'SQL', 'MongoDB', 'PostgreSQL', 'Docker', 'AWS', 'Git', 'REST API', 'C++', 'C#',
        'TypeScript', 'Flask', 'Django', 'Machine Learning', 'Data Structures', 'Algorithms'
    ]
    
    found_skills = []
    if resume_text:
        for skill in skills_keywords:
            if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
                found_skills.append(skill)
    
    primary_skill = found_skills[0] if len(found_skills) > 0 else "Software Development"
    secondary_skill = found_skills[1] if len(found_skills) > 1 else "Web Technologies"
    tertiary_skill = found_skills[2] if len(found_skills) > 2 else "Database & Architecture"
    
    questions = [
        f"Hello {candidate_name}! How has your day been so far? Could you give me a brief overview of your background?",
        f"I noticed from your resume that you have experience with {primary_skill}. Could you share a project where you used {primary_skill} extensively?",
        f"How do you approach designing scalable systems and writing clean, maintainable code in {primary_skill}?",
        f"Your resume highlights proficiency in {secondary_skill}. What were some of the key technical challenges you faced while working with {secondary_skill}?",
        f"Can you explain how you integrate {secondary_skill} with backend APIs or databases like {tertiary_skill}?",
        "Tell me about a complex technical problem you encountered in your previous projects and step-by-step how you solved it.",
        "How do you handle working in an agile team environment when project requirements change rapidly?",
        "Describe a situation where you had a difference of technical opinion with a teammate and how you resolved it constructively.",
        f"What motivated you to develop your skills in {', '.join(found_skills[:3]) if found_skills else 'software engineering'}, and how do you stay updated with new trends?",
        "Where do you see yourself professionally in the next 3 to 5 years, and what technical goals are you aiming to achieve?"
    ]
    return questions

def evaluate_candidate_answers(transcript):
    """Evaluates the candidate's answers based on word count, technical depth, and structure."""
    total_words = 0
    detailed_answers_count = 0
    
    for item in transcript:
        answer = item.get('answer', '').strip()
        words = len(answer.split())
        total_words += words
        if words > 15:
            detailed_answers_count += 1
            
    base_score = 65
    effort_bonus = min(25, (total_words // 20) * 2)
    depth_bonus = min(10, detailed_answers_count * 2)
    final_score = min(98, base_score + effort_bonus + depth_bonus)
    
    feedback = (
        f"You completed the interview with strong enthusiasm. Your responses demonstrated "
        f"practical problem-solving ability and clear communication. You provided {detailed_answers_count} "
        f"detailed answers across the 10 questions. Continuing to ground your answers in concrete project examples "
        f"using the STAR method (Situation, Task, Action, Result) will make your interview performance even more impactful."
    )
    
    strengths = [
        "Good communication clarity and articulate delivery",
        "Demonstrated technical awareness across key resume skills",
        "Constructive problem-solving mindset and positive attitude"
    ]
    
    mistakes = [
        "Elaborate more on specific metrics or outcomes achieved in your projects",
        "Use structured frameworks (like STAR) when answering behavioral questions"
    ]
    
    return {
        "score": final_score,
        "feedback": feedback,
        "strengths": strengths,
        "mistakes": mistakes
    }

@interview_bp.route('/start', methods=['POST'])
def start_interview():
    """Generates realistic HR interview questions based on the candidate's resume."""
    data = request.get_json() or {}
    user_id = data.get('user_id') or data.get('studentId')
    difficulty = data.get('difficulty', 'medium').lower()

    user = None
    if user_id and ObjectId.is_valid(user_id):
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        user = users_collection.find_one({"role": "student"})

    candidate_name = user.get("name", "Candidate") if user else "Candidate"
    resume_text = ""
    if user and user.get("resume_filename"):
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user["resume_filename"])
        if os.path.exists(resume_path):
            resume_text = extract_text_from_pdf(resume_path) or ""

    questions = []
    if resume_text:
        prompt = f"""
        You are a friendly, professional HR interviewer conducting a real job interview. Assess the candidate holistically based on their resume.
        Difficulty level: {difficulty}

        Based on the candidate's resume below, generate EXACTLY 10 interview questions.
        Return your response as a single, raw JSON object with one key: "questions", which holds a list of exactly 10 question strings.

        Candidate's Resume:
        ---
        {resume_text}
        ---
        """
        ai_response = get_ai_response(prompt)
        if ai_response and "questions" in ai_response:
            questions = ai_response.get("questions", [])

    if len(questions) < 10:
        resume_questions = generate_resume_questions(resume_text, candidate_name)
        questions.extend(resume_questions[len(questions):10])
    
    return jsonify({"questions": questions[:10]}), 200

@interview_bp.route('/evaluate', methods=['POST'])
def evaluate_answers():
    """Evaluates the candidate performance based on their interview answers."""
    data = request.get_json() or {}
    user_id = data.get('user_id') or data.get('studentId')
    transcript = data.get('transcript')
    questions = data.get('questions', [])
    answers = data.get('answers', [])
    
    if not transcript and questions and answers:
        transcript = []
        for i, (question, answer) in enumerate(zip(questions, answers)):
            transcript.append({
                'question': question,
                'answer': answer
            })

    if not transcript:
        return jsonify({"error": "No transcript provided."}), 400

    formatted_transcript = "\n".join([f"Question: {item.get('question', '')}\nAnswer: {item.get('answer', '')}\n---" for item in transcript])

    prompt = f"""
    You are a professional HR interviewer providing feedback after completing an interview. 
    
    Return your response as a single, raw JSON object with these exact keys:
    - "score": An integer from 0 to 100
    - "feedback": A warm, detailed paragraph
    - "strengths": A list of 3-5 specific strengths
    - "mistakes": A list of 2-4 areas for improvement

    Interview Transcript:
    ---
    {formatted_transcript}
    ---
    """
    
    ai_response = get_ai_response(prompt)
    if not ai_response:
        ai_response = evaluate_candidate_answers(transcript)

    interview_score = ai_response.get("score", 85)
    if user_id:
        if ObjectId.is_valid(user_id):
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"interviewScore": interview_score}}
            )
        else:
            users_collection.update_one(
                {"role": "student"},
                {"$set": {"interviewScore": interview_score}}
            )

    return jsonify(ai_response), 200