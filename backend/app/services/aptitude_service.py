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

# Normal test length: 10-15 questions per attempt (REVERTED from the old 50).
# Used as the default everywhere a count is not explicitly supplied.
DEFAULT_TEST_QUESTIONS = 15
MAX_TEST_QUESTIONS = 15


def _clamp_test_length(num_questions):
    """Normalize a requested question count to the NORMAL test length.

    None/invalid -> default (15). Any value above the 15-question cap is
    clamped down, so the old 50-question length can never come back through
    any caller. A caller may still ask for fewer (e.g. 10) for a short test.
    """
    try:
        n = int(num_questions)
    except (TypeError, ValueError):
        return DEFAULT_TEST_QUESTIONS
    return max(1, min(n, MAX_TEST_QUESTIONS))


def generate_aptitude_questions(topic, difficulty="medium", num_questions=None):
    """Build the test question pool for a topic.

    Sources, in order: the topic's curated DB bank, then AI-generated
    questions (Gemini via get_ai_response) to EXPAND the pool dynamically so
    retakes are not identical repeats. The final list is shuffled, de-duplicated
    and capped at the normal test length (15 questions). Falls back to the
    curated bank alone when the AI is unavailable - tests never break.
    """
    num_questions = _clamp_test_length(num_questions)
    print(f"[DEBUG] generate_aptitude_questions called for topic: '{topic}' (count={num_questions})")
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
            questions = list(doc["questions"])
    except Exception as e:
        print(f"DB lookup warning for test questions: {e}")

    if not questions and matched_topic in PREDEFINED_TEST_QUESTIONS:
        questions = list(PREDEFINED_TEST_QUESTIONS[matched_topic])

    # NORMAL LENGTH CAP: a finished pool is trimmed to the normal test length
    # (15) so legacy 50-question DB banks can never produce an oversized paper.
    questions = questions[:num_questions]

    # FALLBACK-SWAP GUARD: the old code substituted a different topic's bank
    # ("Number System") when a topic had no questions - that is where the
    # "What is 2+2"-style off-topic trivial questions came from. Never show
    # another topic's questions; keep the pool empty instead so the AI
    # expansion below still runs.

    if questions:
        questions = _dedupe_questions(questions)

    # Dynamic expansion: top up toward the requested size with freshly
    # generated, on-topic questions (bounded effort - never blocks the
    # request if the AI is slow/unavailable).
    if len(questions) < num_questions:
        needed = num_questions - len(questions)
        generated = _generate_ai_questions(matched_topic, difficulty, needed)
        if generated:
            questions.extend(generated)
            questions = _dedupe_questions(questions)
            print(f"[EXPAND] pool expanded with {len(generated)} AI questions "
                  f"for '{matched_topic}' (total {len(questions)})")

    if not questions:
        # Last resort ONLY when the topic truly has no curated bank and AI
        # failed: an empty pool with a clear log (the caller 404s).
        print(f"[WARN] no questions available for topic '{matched_topic}'")

    # Shuffle so two attempts never see the same order/selection.
    random.shuffle(questions)

    print(f"[SUCCESS] Returning {len(questions)} test questions for '{matched_topic}'")
    return {"questions": questions}


def _dedupe_questions(questions):
    """Remove duplicate questions (by normalized question text)."""
    seen = set()
    unique = []
    for q in questions:
        text = (q.get("question") or "").strip().lower() if isinstance(q, dict) else str(q).strip().lower()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(q)
    return unique


def _generate_ai_questions(topic, difficulty, count):
    """Ask the LLM for `count` fresh on-topic questions. Returns [] on any
    failure - the curated bank is always the floor."""
    try:
        count = max(1, min(int(count), MAX_TEST_QUESTIONS))
    except (TypeError, ValueError):
        return []
    prompt = f"""
    You are an aptitude exam setter for placement training.
    Generate exactly {count} multiple-choice aptitude questions on the topic "{topic}"
    at {difficulty} difficulty.

    Rules:
    - Each question must be quantitative/logical and specific to "{topic}".
    - NEVER produce trivial questions (e.g. "What is 2+2?"). Every question
      must require actual reasoning or calculation.
    - Do NOT repeat well-known textbook examples verbatim.

    IMPORTANT: Your entire response must be a single, raw JSON object and nothing else.
    The JSON object must have a single key "questions".
    Each question object must have these exact keys:
    - "question": string
    - "options": list of exactly 4 strings
    - "correct_answer": string that exactly matches one of the options
    - "explanation": short step-by-step solution string
    - "difficulty": "{difficulty}"
    """
    try:
        ai_response = get_ai_response(prompt)
    except Exception as e:
        print(f"[EXPAND] AI question generation failed: {e}")
        return []
    if not ai_response or not isinstance(ai_response, dict):
        return []
    raw = ai_response.get("questions") or []
    valid = []
    for q in raw:
        if (isinstance(q, dict)
                and q.get("question")
                and isinstance(q.get("options"), list)
                and len(q["options"]) >= 2
                and q.get("correct_answer") in q["options"]):
            valid.append({
                "question": q["question"],
                "options": q["options"][:4],
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation", ""),
                "difficulty": q.get("difficulty", difficulty),
                "generated_by": "ai",
            })
    print(f"[EXPAND] AI returned {len(valid)}/{count} valid questions for '{topic}'")
    return valid

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
        practice_questions = list(PREDEFINED_PRACTICE_QUESTIONS[matched_topic])

    # Same fallback-swap guard as tests: never substitute another topic's
    # practice bank (source of off-topic trivial questions).
    if practice_questions:
        practice_questions = _dedupe_questions(practice_questions)
        random.shuffle(practice_questions)
        practice_questions = practice_questions[:max(1, min(int(num_questions or 10), len(practice_questions)))]

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
