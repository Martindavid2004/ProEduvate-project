# aptitude_service.py
import random
from .ai_service import get_ai_response
from .aptitude_config import APTITUDE_TOPICS, SAMPLE_QUESTIONS, VIDEO_RESOURCES

from .aptitude_db_questions import PREDEFINED_PRACTICE_QUESTIONS, PREDEFINED_TEST_QUESTIONS
from ..database import aptitude_practice_collection, aptitude_test_questions_collection

def seed_db_questions():
    """Ensures practice and test questions are seeded into the database."""
    try:
        for topic_name, q_list in PREDEFINED_PRACTICE_QUESTIONS.items():
            existing = aptitude_practice_collection.find_one({"topic": topic_name})
            if not existing:
                aptitude_practice_collection.insert_one({"topic": topic_name, "questions": q_list})

        for topic_name, q_list in PREDEFINED_TEST_QUESTIONS.items():
            existing = aptitude_test_questions_collection.find_one({"topic": topic_name})
            if not existing:
                aptitude_test_questions_collection.insert_one({"topic": topic_name, "questions": q_list})
    except Exception as e:
        print(f"Warning seeding question banks to DB: {e}")

def generate_aptitude_questions(topic, difficulty="medium", num_questions=50):
    """Fetches aptitude test questions from DB (No Gemini AI call)."""
    print(f"[DEBUG] generate_aptitude_questions called for topic: '{topic}'")
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            break
    
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        return None
    
    seed_db_questions()

    questions = []
    try:
        doc = aptitude_test_questions_collection.find_one({"topic": matched_topic})
        if doc and "questions" in doc:
            questions = doc["questions"]
    except Exception as e:
        print(f"DB lookup warning for test questions: {e}")

    if not questions and matched_topic in PREDEFINED_TEST_QUESTIONS:
        questions = PREDEFINED_TEST_QUESTIONS[matched_topic]

    if not questions:
        questions = PREDEFINED_TEST_QUESTIONS.get("Number System", [])

    print(f"[SUCCESS] Retrieved {len(questions)} test questions from DB for '{matched_topic}'")
    return {"questions": questions}

def generate_practice_questions(topic, num_questions=10):
    """Fetches practice questions with detailed solutions from DB (No Gemini AI call)."""
    print(f"[DEBUG] generate_practice_questions called for topic: '{topic}'")
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            break
    
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        return None
    
    seed_db_questions()

    practice_questions = []
    try:
        doc = aptitude_practice_collection.find_one({"topic": matched_topic})
        if doc and "questions" in doc:
            practice_questions = doc["questions"]
    except Exception as e:
        print(f"DB lookup warning for practice questions: {e}")

    if not practice_questions and matched_topic in PREDEFINED_PRACTICE_QUESTIONS:
        practice_questions = PREDEFINED_PRACTICE_QUESTIONS[matched_topic]

    if not practice_questions:
        practice_questions = PREDEFINED_PRACTICE_QUESTIONS.get("Number System", [])

    print(f"[SUCCESS] Retrieved {len(practice_questions)} practice questions from DB for '{matched_topic}'")
    return {"practice_questions": practice_questions}

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

from .aptitude_db_concepts import PREDEFINED_CONCEPTS
from ..database import aptitude_concepts_collection

def seed_db_concepts():
    """Ensures all topic concepts are stored in the database."""
    try:
        for topic_name, concept_data in PREDEFINED_CONCEPTS.items():
            existing = aptitude_concepts_collection.find_one({"topic": topic_name})
            if not existing:
                aptitude_concepts_collection.insert_one(dict(concept_data))
    except Exception as e:
        print(f"Warning seeding aptitude concepts to DB: {e}")

def get_topic_concepts(topic):
    """Fetches learning concepts for a topic directly from the Database (no AI generation)."""
    print(f"[DEBUG] get_topic_concepts called for topic: '{topic}'")
    matched_topic = None
    for key in APTITUDE_TOPICS.keys():
        if key.lower() == topic.lower():
            matched_topic = key
            break
            
    if not matched_topic:
        print(f"[ERROR] Topic '{topic}' not found in APTITUDE_TOPICS")
        return None

    # Try fetching directly from MongoDB
    try:
        concept_doc = aptitude_concepts_collection.find_one({"topic": matched_topic})
        if concept_doc:
            concept_doc.pop("_id", None)
            print(f"[SUCCESS] Retrieved concepts for '{matched_topic}' from Database")
            return concept_doc
    except Exception as e:
        print(f"DB lookup warning: {e}")

    # Seed DB and retry
    seed_db_concepts()
    try:
        concept_doc = aptitude_concepts_collection.find_one({"topic": matched_topic})
        if concept_doc:
            concept_doc.pop("_id", None)
            return concept_doc
    except Exception as e:
        print(f"DB lookup warning after seed: {e}")

    # Fallback directly to predefined concepts dictionary
    if matched_topic in PREDEFINED_CONCEPTS:
        print(f"[SUCCESS] Retrieved concepts for '{matched_topic}' from predefined DB dictionary")
        return PREDEFINED_CONCEPTS[matched_topic]

    return None

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
