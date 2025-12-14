from flask import Blueprint, jsonify, request
# Import the service that communicates with the AI
from ..services.ai_service import get_ai_response, get_general_chat_response, get_quiz_fallback

chatbot_bp = Blueprint('chatbot_bp', __name__, url_prefix='/api/chatbot')

@chatbot_bp.route('/query', methods=['POST'])
def handle_chat_query():
    """Generates an MCQ quiz based on a topic from the user."""
    data = request.get_json()
    topic = data.get('topic')
    num_questions = data.get('num_questions', 5)

    if not topic:
        return jsonify({"error": "No topic provided."}), 400

    # Ensure num_questions is within reasonable bounds
    num_questions = max(1, min(int(num_questions), 10))

    try:
        # Craft a specific prompt for the AI to generate an MCQ quiz
        prompt = f"""
        You are an AI assistant creating a practice quiz for a student.
        Based on the topic "{topic}", generate exactly {num_questions} multiple-choice questions (MCQs).

        IMPORTANT: Your entire response must be a single, raw JSON object and nothing else.
        The JSON object must have a single key "questions".
        The value of "questions" must be a list of exactly {num_questions} question objects.
        Each question object must have these exact keys:
        - "question": A string with the question text.
        - "options": A list of exactly 4 strings representing the possible answers.
        - "correct_answer": A string that is an exact match to one of the options.

        Make the questions educational and appropriate for beginners to intermediate level.
        Ensure all questions are related to {topic}.
        """
        
        print(f"Generating quiz for topic: {topic}, questions: {num_questions}")
        ai_response = get_ai_response(prompt)
        
        # Check if AI response is valid
        if ai_response and "questions" in ai_response and len(ai_response["questions"]) > 0:
            # Validate the structure of each question
            valid_questions = []
            for q in ai_response["questions"]:
                if (isinstance(q, dict) and 
                    "question" in q and 
                    "options" in q and 
                    "correct_answer" in q and
                    isinstance(q["options"], list) and
                    len(q["options"]) >= 4 and
                    q["correct_answer"] in q["options"]):
                    valid_questions.append(q)
            
            if valid_questions:
                print(f"Successfully generated {len(valid_questions)} valid questions")
                return jsonify({"questions": valid_questions[:num_questions]}), 200
        
        # If AI fails or returns invalid data, use fallback
        print("AI response invalid, using fallback quiz generation")
        fallback_response = get_quiz_fallback(topic, num_questions)
        return jsonify(fallback_response), 200
        
    except Exception as e:
        print(f"Error in quiz generation: {e}")
        # Use fallback on any error
        fallback_response = get_quiz_fallback(topic, num_questions)
        return jsonify(fallback_response), 200

@chatbot_bp.route('/general_query', methods=['POST'])
def handle_general_query():
    """Handles general chat conversations with the AI assistant."""
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "No prompt provided."}), 400

    try:
        ai_response = get_general_chat_response(prompt)
        return jsonify({"answer": ai_response}), 200
    except Exception as e:
        print(f"Error in general chat: {e}")
        return jsonify({"error": "Failed to get AI response."}), 500

@chatbot_bp.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    """Generate quiz questions for teacher assignments."""
    data = request.get_json()
    topic = data.get('topic')
    num_questions = data.get('num_questions', 10)

    if not topic:
        return jsonify({"error": "No topic provided."}), 400

    # Ensure num_questions is within reasonable bounds
    num_questions = max(1, min(int(num_questions), 20))

    try:
        # Craft a specific prompt for the AI to generate an MCQ quiz
        prompt = f"""
        You are an AI assistant creating a quiz for students.
        Based on the topic "{topic}", generate exactly {num_questions} multiple-choice questions (MCQs).

        IMPORTANT: Your entire response must be a single, raw JSON object and nothing else.
        The JSON object must have a single key "questions".
        The value of "questions" must be a list of exactly {num_questions} question objects.
        Each question object must have these exact keys:
        - "question": A string with the question text.
        - "options": A list of exactly 4 strings representing the possible answers.
        - "correct_answer": A string that is an exact match to one of the options.

        Make the questions educational and appropriate for students.
        Ensure all questions are related to {topic}.
        """
        
        print(f"Generating quiz for topic: {topic}, questions: {num_questions}")
        ai_response = get_ai_response(prompt)
        
        # Check if AI response is valid
        if ai_response and "questions" in ai_response and len(ai_response["questions"]) > 0:
            # Validate the structure of each question
            valid_questions = []
            for q in ai_response["questions"]:
                if (isinstance(q, dict) and 
                    "question" in q and 
                    "options" in q and 
                    "correct_answer" in q and
                    isinstance(q["options"], list) and
                    len(q["options"]) >= 4 and
                    q["correct_answer"] in q["options"]):
                    valid_questions.append(q)
            
            if valid_questions:
                print(f"Successfully generated {len(valid_questions)} valid questions")
                return jsonify({"questions": valid_questions[:num_questions]}), 200
        
        # If AI fails or returns invalid data, use fallback
        print("AI response invalid, using fallback quiz generation")
        fallback_response = get_quiz_fallback(topic, num_questions)
        return jsonify(fallback_response), 200
        
    except Exception as e:
        print(f"Error in quiz generation: {e}")
        # Use fallback on any error
        fallback_response = get_quiz_fallback(topic, num_questions)
        return jsonify(fallback_response), 200