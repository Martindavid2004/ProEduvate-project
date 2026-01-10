# aptitude_service.py
import random
from .ai_service import get_ai_response
from .aptitude_config import APTITUDE_TOPICS, SAMPLE_QUESTIONS, VIDEO_RESOURCES

def generate_aptitude_questions(topic, difficulty="medium", num_questions=50):
    """Generate aptitude questions using AI based on topic and difficulty"""
    
    print(f"[DEBUG] generate_aptitude_questions called with topic: '{topic}'")
    print(f"[DEBUG] Available topics: {list(APTITUDE_TOPICS.keys())}")
    
    # Normalize topic name for matching
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            print(f"[DEBUG] Matched topic '{topic}' to '{matched_topic}'")
            break
    
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        print(f"[ERROR] Available topics: {list(APTITUDE_TOPICS.keys())}")
        return None
    
    prompt = f"""
    Generate {num_questions} multiple-choice aptitude questions on the topic: {matched_topic}.
    
    Difficulty level: {difficulty}
    
    Each question should be unique and test different aspects of {matched_topic}.
    
    Return a JSON object with this exact structure:
    {{
        "questions": [
            {{
                "question": "Question text here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "The correct option text",
                "explanation": "Brief explanation of the answer",
                "difficulty": "{difficulty}"
            }}
        ]
    }}
    
    Make the questions progressively challenging.
    Ensure all options are plausible.
    Provide clear explanations for each answer.
    
    IMPORTANT: Do NOT use markdown formatting like ** for bold or * for italics.
    Use plain text only. The text should be readable without any markdown syntax.
    """
    
    result = get_ai_response(prompt)
    
    # Post-process to remove any markdown formatting
    if result and isinstance(result, dict):
        result = _remove_markdown_formatting(result)
    
    return result

def generate_practice_questions(topic, num_questions=10):
    """Generate practice questions with detailed solutions"""
    
    print(f"[DEBUG] generate_practice_questions called with topic: '{topic}'")
    print(f"[DEBUG] Available topics: {list(APTITUDE_TOPICS.keys())}")
    
    # Normalize topic name for matching
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            print(f"[DEBUG] Matched topic '{topic}' to '{matched_topic}'")
            break
    
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        print(f"[ERROR] Available topics: {list(APTITUDE_TOPICS.keys())}")
        return None
    
    prompt = f"""
    Generate {num_questions} practice questions on {matched_topic} with step-by-step solutions.
    
    Return a JSON object with this exact structure:
    {{
        "practice_questions": [
            {{
                "question": "Question text",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Correct option",
                "step_by_step_solution": "Detailed solution with steps",
                "tips_and_tricks": "Shortcut methods or tricks",
                "difficulty": "easy/medium/hard"
            }}
        ]
    }}
    
    Focus on common patterns and frequently asked questions in aptitude tests.
    
    IMPORTANT: Do NOT use markdown formatting like ** for bold or * for italics.
    Use plain text only. The text should be readable without any markdown syntax.
    """
    
    result = get_ai_response(prompt)
    
    # Post-process to remove any markdown formatting
    if result and isinstance(result, dict):
        result = _remove_markdown_formatting(result)
    
    return result

def evaluate_aptitude_test(questions, user_answers):
    """Evaluate user's aptitude test answers"""
    
    total_questions = len(questions)
    correct_answers = 0
    incorrect_answers = 0
    unanswered = 0
    
    results = []
    
    for i, question in enumerate(questions):
        user_answer = user_answers.get(str(i), None)
        correct_answer = question.get('correct_answer')
        
        is_correct = user_answer == correct_answer
        
        if user_answer is None:
            unanswered += 1
            status = "unanswered"
        elif is_correct:
            correct_answers += 1
            status = "correct"
        else:
            incorrect_answers += 1
            status = "incorrect"
        
        results.append({
            "question_number": i + 1,
            "question": question.get('question'),
            "options": question.get('options'),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "explanation": question.get('explanation'),
            "status": status
        })
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers,
        "unanswered": unanswered,
        "score": round(score, 2),
        "percentage": round(score, 2),
        "results": results,
        "performance": get_performance_analysis(score)
    }

def get_performance_analysis(score):
    """Provide performance analysis based on score"""
    if score >= 90:
        return {
            "level": "Excellent",
            "message": "Outstanding performance! You have mastered this topic.",
            "recommendation": "Try harder topics or help others learn."
        }
    elif score >= 75:
        return {
            "level": "Very Good",
            "message": "Great job! You have a strong understanding.",
            "recommendation": "Practice a few more challenging problems."
        }
    elif score >= 60:
        return {
            "level": "Good",
            "message": "Good effort! You're on the right track.",
            "recommendation": "Review the concepts and practice more."
        }
    elif score >= 40:
        return {
            "level": "Average",
            "message": "You need more practice on this topic.",
            "recommendation": "Go through video tutorials and practice questions."
        }
    else:
        return {
            "level": "Needs Improvement",
            "message": "Keep practicing! Everyone starts somewhere.",
            "recommendation": "Start with basics and work through examples step by step."
        }

def get_topic_concepts(topic):
    """Get learning concepts and tricks for a topic"""
    
    print(f"[DEBUG] get_topic_concepts called with topic: '{topic}'")
    print(f"[DEBUG] Available topics: {list(APTITUDE_TOPICS.keys())}")
    
    # Normalize topic name for matching
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            print(f"[DEBUG] Matched topic '{topic}' to '{matched_topic}'")
            break
    
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        print(f"[ERROR] Available topics: {list(APTITUDE_TOPICS.keys())}")
        return None
    
    prompt = f"""
    Provide comprehensive learning material for the aptitude topic: {matched_topic}
    
    Return a JSON object with this structure:
    {{
        "topic": "{matched_topic}",
        "concepts": [
            {{
                "title": "Concept name",
                "description": "Detailed explanation",
                "formula": "Any relevant formulas",
                "example": "Example with solution"
            }}
        ],
        "tips_and_tricks": [
            "Shortcut 1",
            "Shortcut 2",
            "Common pitfalls to avoid"
        ],
        "key_points": [
            "Important point 1",
            "Important point 2"
        ]
    }}
    
    Make it comprehensive but easy to understand for students.
    
    IMPORTANT: Do NOT use markdown formatting like ** for bold or * for italics. 
    Use plain text only. The text should be readable without any markdown syntax.
    """
    
    result = get_ai_response(prompt)
    
    # Post-process to remove any markdown formatting that might still appear
    if result and isinstance(result, dict):
        result = _remove_markdown_formatting(result)
    
    return result

def _remove_markdown_formatting(data):
    """Recursively remove markdown formatting from strings in dictionary/list"""
    if isinstance(data, dict):
        return {key: _remove_markdown_formatting(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_remove_markdown_formatting(item) for item in data]
    elif isinstance(data, str):
        # Remove bold formatting
        text = data.replace('**', '')
        # Remove italic formatting
        text = text.replace('*', '')
        # Remove other common markdown
        text = text.replace('__', '')
        text = text.replace('_', '')
        return text
    else:
        return data

def get_topics_list():
    """Get list of all available aptitude topics"""
    return [
        {
            "name": topic,
            "description": details["description"],
            "video_url": VIDEO_RESOURCES.get(topic, ""),
            "has_practice": topic in SAMPLE_QUESTIONS
        }
        for topic, details in APTITUDE_TOPICS.items()
    ]
