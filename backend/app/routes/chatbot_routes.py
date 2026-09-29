from flask import Blueprint, jsonify, request
# Import the service that communicates with the AI
from ..services.ai_service import get_ai_response, get_general_chat_response
from ..services.question_bank import pick_mixed_questions, pick_questions, get_categories


# Shared validator: every generated/bank question must be well-formed before
# it reaches a student. Malformed LLM output is dropped, never shown.
def _valid_question(q):
    return (isinstance(q, dict)
            and q.get("question")
            and isinstance(q.get("options"), list)
            and len(q.get("options")) >= 2
            and q.get("correct_answer") in q["options"])


def _dedupe(questions):
    seen = set()
    unique = []
    for q in questions:
        text = (q.get("question") or "").strip().lower()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(q)
    return unique

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
        # Craft a specific prompt for the AI to generate an MCQ quiz.
        # Explicit anti-triviality rules: the LLM must never emit "2+2"-style
        # filler - that is what used to make every attempt feel identical.
        prompt = f"""
        You are an AI assistant creating a practice quiz for a student.
        Based on the topic "{topic}", generate exactly {num_questions} multiple-choice questions (MCQs).

        Rules:
        - Every question must require real understanding of {topic}.
        - NEVER produce trivial or filler questions (e.g. "What is 2+2?",
          "Capital of France" style generalities unless {topic} IS general knowledge).
        - Do not repeat well-known textbook examples verbatim.

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
            valid_questions = [q for q in ai_response["questions"] if _valid_question(q)]
            
            if valid_questions:
                print(f"Successfully generated {len(valid_questions)} valid questions")
                return jsonify({"questions": _dedupe(valid_questions)[:num_questions]}), 200
        
        # If AI fails or returns invalid data, fall back to the categorized
        # dynamic bank (random selection per request) - NEVER to the old
        # static placeholder questions ("Concept A/B/C/D" fillers).
        print("AI response invalid, using categorized question bank fallback")
        fallback = pick_mixed_questions(num_questions)
        return jsonify({"questions": fallback}), 200
        
    except Exception as e:
        print(f"Error in quiz generation: {e}")
        # Use categorized bank on any error
        fallback = pick_mixed_questions(num_questions)
        return jsonify({"questions": fallback}), 200

@chatbot_bp.route('/general_query', methods=['POST'])
def handle_general_query():
    """Handles general chat conversations with the AI assistant."""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt') or data.get('message')

        if not prompt:
            return jsonify({"error": "No prompt provided."}), 400

        if isinstance(prompt, dict):
            prompt_str = prompt.get('prompt') or prompt.get('message') or str(prompt)
        else:
            prompt_str = str(prompt)

        ai_response = get_general_chat_response(prompt_str)
        if not ai_response or "Error:" in ai_response:
            ai_response = "Thank you for sharing your response. Great progress!"

        return jsonify({
            "answer": ai_response,
            "response": ai_response,
            "success": True
        }), 200
    except Exception as e:
        print(f"Error in general chat: {e}")
        default_feedback = "Thank you for sharing your response. Great effort!"
        return jsonify({
            "answer": default_feedback,
            "response": default_feedback,
            "success": True
        }), 200

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

    # Optional category filter (Grammar / General Knowledge / Technical /
    # Logical Reasoning). When provided, the generated paper sticks to the
    # requested categories and the bank fallback filters the same way.
    categories = data.get('categories') or None

    # source='bank': draw directly from the seeded local question bank
    # (NO AI call). Deterministic offline path for assignments - the bank is
    # already categorized, vetted and randomly selected per generation.
    if str(data.get('source') or '').lower() == 'bank':
        try:
            bank_questions = pick_questions(num_questions, categories=categories)
            print(f"Served {len(bank_questions)} questions from the seeded "
                  f"local question bank (no AI)")
            return jsonify({"questions": bank_questions}), 200
        except Exception as bank_err:
            print(f"Question bank selection failed: {bank_err}")
            return jsonify({"error": "Failed to select questions from the bank"}), 500

    try:
        # Craft a specific prompt for the AI to generate an MCQ quiz.
        # Explicit anti-triviality rules: the LLM must never emit "2+2"-style
        # filler - that is what used to make every attempt feel identical.
        category_rule = (f"\n        Every question must belong to one of these categories: {', '.join(categories)}."
                         if categories else "")
        prompt = f"""
        You are an AI assistant creating a quiz for students.
        Based on the topic "{topic}", generate exactly {num_questions} multiple-choice questions (MCQs).

        Rules:
        - Every question must require real reasoning or subject knowledge.
        - NEVER produce trivial or filler questions (e.g. "What is 2+2?",
          "Capital of France" style generalities unless the topic IS general knowledge).
        - Do not repeat well-known textbook examples verbatim.{category_rule}

        IMPORTANT: Your entire response must be a single, raw JSON object and nothing else.
        The JSON object must have a single key "questions".
        The value of "questions" must be a list of exactly {num_questions} question objects.
        Each question object must have these exact keys:
        - "question": A string with the question text.
        - "options": A list of exactly 4 strings representing the possible answers.
        - "correct_answer": A string that is an exact match to one of the options.
        - "category": One of {', '.join(get_categories())} (best match for the question).

        Make the questions educational and appropriate for students.
        Ensure all questions are related to {topic}.
        """
        
        print(f"Generating quiz for topic: {topic}, questions: {num_questions}, "
              f"categories: {categories or 'all'}")
        ai_response = get_ai_response(prompt)
        
        # Check if AI response is valid
        if ai_response and "questions" in ai_response and len(ai_response["questions"]) > 0:
            valid_questions = [q for q in ai_response["questions"] if _valid_question(q)]
            
            if valid_questions:
                print(f"Successfully generated {len(valid_questions)} valid questions")
                return jsonify({"questions": _dedupe(valid_questions)[:num_questions]}), 200
        
        # If AI fails or returns invalid data, fall back to the categorized
        # dynamic bank (random selection per request) - NEVER to the old
        # static placeholder questions ("Concept A/B/C/D" fillers).
        print("AI response invalid, using categorized question bank fallback")
        fallback = pick_questions(num_questions, categories=categories)
        return jsonify({"questions": fallback}), 200
        
    except Exception as e:
        print(f"Error in quiz generation: {e}")
        # Use categorized bank on any error
        fallback = pick_questions(num_questions, categories=categories)
        return jsonify({"questions": fallback}), 200


@chatbot_bp.route('/quiz_categories', methods=['GET'])
def quiz_categories():
    """List the available question-bank categories for quiz creation."""
    return jsonify({"success": True, "categories": get_categories()}), 200