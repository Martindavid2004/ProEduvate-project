import re
from flask import Blueprint, jsonify, request, current_app
from ..database import users_collection, submissions_collection
from bson import ObjectId
import os
from datetime import datetime
from ..services.ai_service import (
    extract_resume_text, get_ai_response,
    generate_interview_questions_ollama, _validate_questions_payload,
    _format_question_for_interview,
)
from ..services.interview_service import evaluate_interview

interview_bp = Blueprint('interview_bp', __name__, url_prefix='/api/interview')

# Skills/technologies recognised by the offline fallback generator. Questions
# produced here reference ONLY terms actually matched in the resume text.
_SKILLS_KEYWORDS = [
    'Java', 'Python', 'JavaScript', 'React', 'Node.js', 'Spring Boot', 'HTML', 'CSS',
    'SQL', 'MongoDB', 'PostgreSQL', 'MySQL', 'Docker', 'AWS', 'Git', 'REST API',
    'C++', 'C#', 'TypeScript', 'Flask', 'Django', 'FastAPI', 'Machine Learning',
    'Data Structures', 'Algorithms', 'Kubernetes', 'Linux', 'GraphQL', 'Redux'
]

# Project headers like "MedVision AI - FastAPI, React, MongoDB" or
# "MedVision AI | FastAPI React MongoDB": captures the project name and its
# tech list so the fallback can ask grounded, project-specific questions.
_PROJECT_HEADER = re.compile(
    r'^\s*([A-Z][A-Za-z0-9 .&+]{2,40}?)\s*[\-\u2013\u2014:|]\s*(.+)$')


def _extract_resume_highlights(resume_text):
    """Extract skills and project names/tech-stacks actually present in the resume.

    Returns (found_skills, projects) where projects is a list of
    (project_name, tech_string). Used ONLY by the offline fallback generator;
    nothing is invented that is not in the resume text.
    """
    found_skills = []
    projects = []
    if not resume_text:
        return found_skills, projects

    for skill in _SKILLS_KEYWORDS:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            found_skills.append(skill)

    for line in resume_text.splitlines():
        line = line.strip()
        if not line or len(line) > 120:
            continue
        m = _PROJECT_HEADER.match(line)
        if m:
            name, tech = m.group(1).strip(), m.group(2).strip()
            # Skip lines that look like section headers rather than projects
            if not re.search(r'(education|experience|skills|certification|achievement)',
                             name, re.IGNORECASE):
                projects.append((name, tech))
    return found_skills, projects


def generate_resume_questions(resume_text, candidate_name="Candidate"):
    """Offline fallback question generator, grounded ONLY in the resume.

    Used when the LLM question generation is unavailable or returns too few
    questions. Every question references skills/projects actually matched in
    the resume text. No greetings/introductions: the interviewer speaks only
    real questions (TTS requirement).
    """
    found_skills, projects = _extract_resume_highlights(resume_text)

    primary_skill = found_skills[0] if len(found_skills) > 0 else None
    secondary_skill = found_skills[1] if len(found_skills) > 1 else None
    tertiary_skill = found_skills[2] if len(found_skills) > 2 else None

    questions = []

    # Project-specific questions first (architecture, contribution,
    # challenges, decisions, results) - always grounded in a real project.
    for proj_name, tech in projects[:4]:
        questions.append(
            f"I see {proj_name} in your resume"
            + (f", built with {tech}" if tech else "")
            + ". Can you explain the architecture and the technologies you used?")
        questions.append(
            f"What was your specific contribution to {proj_name}, and what was "
            "the most difficult challenge you faced while building it?")

    if primary_skill:
        questions.append(
            f"Your resume lists {primary_skill}. Can you walk me through a project "
            f"where you used {primary_skill} and the decisions you made?")
    if secondary_skill:
        questions.append(
            f"How did you use {secondary_skill} in your work, and what practical "
            "limitations of it did you encounter?")
    if tertiary_skill:
        questions.append(
            f"Can you explain how you integrated {tertiary_skill} with the rest of "
            "your application's backend or database layer?")

    # General-but-professional questions to fill remaining slots. These are
    # asked only when resume-specific material has been exhausted (or when no
    # resume is available). The list is long enough to always produce 10
    # questions even for an empty resume.
    filler = [
        "Tell me about a complex technical problem you encountered in your projects and step-by-step how you solved it.",
        "How do you handle working in a team when project requirements change rapidly?",
        "Describe a situation where you had a difference of technical opinion with a teammate and how you resolved it.",
        "What area of your technical skills are you currently strengthening, and how?",
        "Where do you see yourself professionally in the next 3 to 5 years?",
        "Walk me through the project you are most proud of: what problem did it solve and what was your role?",
        "How do you approach debugging when something in your application stops working?",
        "Tell me about a time you had to learn a new technology quickly. How did you do it?",
        "How do you ensure the quality and maintainability of the code you write?",
        "What motivates you about pursuing a career in software development?",
    ]
    for q in filler:
        if len(questions) >= 10:
            break
        questions.append(q)

    return questions[:10]

def _find_interview_session(session_id, user_id=None):
    """Locate an existing interview session (stored in submissions_collection)."""
    if not session_id or not ObjectId.is_valid(session_id):
        return None
    query = {"_id": ObjectId(session_id), "type": "interview_session"}
    if user_id:
        query["student_id"] = str(user_id)
    return submissions_collection.find_one(query)


def _serialize_interview_session(session):
    if not session:
        return None
    return {
        "sessionId": str(session["_id"]),
        "status": session.get("status", "in_progress"),
        "questions": session.get("questions") or [],
        "answers": session.get("answers") or [],
        "answer_turns": session.get("answer_turns") or [],
        "currentQuestionIndex": len(session.get("answers") or []),
        "mode": session.get("mode"),
        "result": session.get("result"),
        "startedAt": session.get("started_at").isoformat()
        if isinstance(session.get("started_at"), datetime) else session.get("started_at"),
        "completedAt": session.get("completed_at").isoformat()
        if isinstance(session.get("completed_at"), datetime) else session.get("completed_at"),
    }


def _resolve_interview_user(user_id):
    """Resolve the interview candidate strictly from the given user_id.

    Never falls back to a random student: that used to store questions/answers
    and the final score against the wrong user.
    """
    if user_id and ObjectId.is_valid(user_id):
        return users_collection.find_one({"_id": ObjectId(user_id)})
    return None


@interview_bp.route('/session/<session_id>', methods=['GET'])
def get_interview_session(session_id):
    """Fetch an interview session state (used on page refresh to resume)."""
    session = _find_interview_session(session_id)
    if not session:
        return jsonify({"error": "Interview session not found"}), 404
    return jsonify({"success": True, "session": _serialize_interview_session(session)}), 200


@interview_bp.route('/start', methods=['POST'])
def start_interview():
    """Generates realistic HR interview questions based on the candidate's resume.

    Idempotent: passing an existing sessionId resumes that session instead of
    creating a duplicate; refreshing mid-interview continues where the student
    left off. The final evaluation is stored on the session record.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id') or data.get('studentId')
    difficulty = data.get('difficulty', 'medium').lower()
    session_id = data.get('session_id') or data.get('sessionId')
    mode = data.get('mode')

    user = _resolve_interview_user(user_id)

    # --- RESUME UPLOAD GATEWAY (server-side) ---
    # The interview questions are generated from the candidate's resume text.
    # Starting without one would silently produce generic questions, so the
    # backend now hard-requires an uploaded resume BEFORE any session is
    # created. The frontend enforces the same gate earlier in the flow
    # (mandatory upload step before duration/type selection).
    # Refresh-safe: resuming an EXISTING session is still allowed even if the
    # gate state changed, so an in-flight interview is never bricked.
    if not (user or {}).get("resume_text") and not (user or {}).get("resume_filename"):
        has_session_request = bool(session_id)
        if not has_session_request:
            return jsonify({
                "success": False,
                "error": "A resume is required before starting the AI Interview.",
                "message": "A resume is required before starting the AI Interview. Please upload your resume first.",
                "code": "RESUME_REQUIRED",
            }), 400

    # --- Resume an existing session when requested (refresh-safe) ---
    existing = _find_interview_session(session_id, user_id)
    if existing:
        if existing.get("status") == "completed":
            return jsonify({
                "success": True,
                "session": _serialize_interview_session(existing),
                "completed": True,
            }), 200
        if mode and not existing.get("mode"):
            submissions_collection.update_one(
                {"_id": existing["_id"]}, {"$set": {"mode": mode}})
            existing["mode"] = mode
        return jsonify({
            "success": True,
            "session": _serialize_interview_session(existing),
            "completed": False,
        }), 200

    # MUST be initialized before the AI branches below: when the LLM call
    # fails, `questions` is never assigned in the branch, and because it is
    # assigned later (questions[:10]), Python treats it as function-local
    # everywhere -> UnboundLocalError -> 500. Found by the live E2E run.
    questions = []

    candidate_name = user.get("name", "Candidate") if user else "Candidate"

    # --- Resume context: REUSE the stored extraction, no second pipeline ---
    # upload_resume (student_routes.py) already extracts and stores
    # user.resume_text at upload time. Fall back to re-reading the stored file
    # only for users whose resume predates that persistence.
    resume_text = (user or {}).get("resume_text") or ""
    if resume_text:
        print(f"[INTERVIEW] Resume context loaded from stored resume_text "
              f"(user={candidate_name!r})")
    else:
        resume_path = None
        if user and user.get("resume_filename"):
            resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                       user["resume_filename"])
        extracted = extract_resume_text(resume_path) if resume_path else None
        if extracted:
            resume_text = extracted
            # Backfill so future starts reuse the stored copy.
            try:
                users_collection.update_one(
                    {"_id": user["_id"]}, {"$set": {"resume_text": resume_text}})
            except Exception as exc:
                print(f"[INTERVIEW] resume_text backfill failed: {exc}")
            print(f"[INTERVIEW] Resume context loaded from resume file re-extraction")
        else:
            # Missing resume must NOT crash the interview - fall back to the
            # existing generic-question behavior.
            print("[INTERVIEW] Resume context unavailable - falling back to "
                  "generic questions")

    if resume_text:
        resume_chars = len(resume_text)
        print(f"[INTERVIEW] Resume characters: {resume_chars}")
        # Guard against pathological resumes: only send the most recent chunk
        # (resumes longer than this are anomalous; the head carries the
        # education/skills/projects sections).
        resume_context = resume_text[:12000]

        # --- PRIMARY: local Ollama LLM (resume-grounded, mixed difficulty) ---
        # The Ollama prompt enforces the required Easy 40% / Medium 40% /
        # Hard 20% mix, so the difficulty is baked into the deck itself.
        ollama_questions = generate_interview_questions_ollama(
            resume_context, difficulty=difficulty, num_questions=10)
        if ollama_questions:
            questions = [q for q in ollama_questions if isinstance(q, str) and q.strip()]
            print(f"[INTERVIEW] Generated {len(questions)} questions via Ollama "
                  f"(model, easy/medium/hard mix)")

        # --- FALLBACK 1: Gemini (same distribution rules) ---
        if not questions:
            prompt = f"""
        You are an AI interviewer. Generate the next interview question using ONLY information supported by the candidate's resume and the current interview context.

        Candidate Resume:
        ---
        {resume_context}
        ---

        Rules:
        1. Ask questions based on projects, skills, education, internships, experience, or technologies actually present in the resume.
        2. Do not invent projects, companies, technologies, certifications, or experience.
        3. Do not ask generic unrelated questions when resume-specific questions are possible.
        4. Questions should be appropriate for the candidate's experience level.
        5. Avoid repeatedly asking the same question.
        6. Follow the natural progression of an interview.
        7. If a project is mentioned, questions may ask about: architecture, technologies used, the candidate's contribution, challenges, decisions, implementation, results, debugging, scalability, lessons learned.
        8. If a technology is listed, questions can test practical understanding of that technology.
        9. Never claim that the candidate has experience with something that is not present in the resume.
        10. Each question must be a single, direct interview question with NO greetings, NO introductions (never say who you are), NO pleasantries and NO commentary. Output ONLY the question text.
        11. Difficulty level: {difficulty}

        Required difficulty distribution: 4 EASY questions (fundamental concepts of listed skills/tools), 4 MEDIUM questions (practical application, implementation and debugging in their projects) and 2 HARD questions (system design trade-offs, scalability, edge cases, situational judgement applied to their projects).

        Generate EXACTLY 10 interview questions from this resume. Return your response as a single, raw JSON object with one key: "questions", which holds a list of exactly 10 question strings.
        """
            print("[INTERVIEW] Generating questions using resume context (Gemini)")
            ai_response = get_ai_response(prompt)
            if ai_response and "questions" in ai_response:
                questions = [q for q in ai_response.get("questions", [])
                             if isinstance(q, str) and q.strip()]
                print(f"[INTERVIEW] Generated {len(questions)} questions from resume (Gemini)")

        # --- FALLBACK 2: offline resume-grounded generator ---
        if not questions:
            print("[INTERVIEW] AI question generation failed - using resume-grounded fallback")
            questions = generate_resume_questions(resume_text, candidate_name)
    else:
        prompt = f"""
        You are an AI interviewer. No resume is available for this candidate.

        Rules:
        1. Ask standard, professional interview questions appropriate for a software role: problem solving, projects described verbally, teamwork, learning, and career goals.
        2. Do NOT invent or assume any specific project, company, technology, certification, or experience for the candidate.
        3. Each question must be a single, direct interview question with NO greetings, NO introductions, NO pleasantries and NO commentary. Output ONLY the question text.
        4. Difficulty level: {difficulty}

        Required difficulty distribution: 4 EASY questions, 4 MEDIUM questions and 2 HARD questions.

        Generate EXACTLY 10 interview questions. Return your response as a single, raw JSON object with one key: "questions", which holds a list of exactly 10 question strings.
        """
        print("[INTERVIEW] Generating questions WITHOUT resume context")
        ai_response = get_ai_response(prompt)
        if ai_response and "questions" in ai_response:
            questions = [q for q in ai_response.get("questions", [])
                         if isinstance(q, str) and q.strip()]

    if len(questions) < 10:
        resume_questions = generate_resume_questions(resume_text, candidate_name)
        questions.extend(resume_questions[len(questions):10])
    questions = questions[:10]

    # Persist the session so refreshes resume it and results have a home.
    session_doc = {
        "type": "interview_session",
        "student_id": str(user_id) if user_id else None,
        "mode": mode,
        "difficulty": difficulty,
        "status": "in_progress",
        "questions": questions,
        "answers": [],
        "answer_turns": [],
        "result": None,
        "started_at": datetime.utcnow(),
        "completed_at": None,
    }
    result = submissions_collection.insert_one(session_doc)

    if questions:
        print(f"[INTERVIEW] Generated question: {questions[0]}")

    return jsonify({
        "success": True,
        "questions": questions,
        "session": _serialize_interview_session(session_doc | {"_id": result.inserted_id}),
    }), 200

@interview_bp.route('/answer', methods=['POST'])
def save_interview_answer():
    """Persist one answer turn so a refresh mid-interview keeps progress.

    Rich persistence: each answer is stored as a structured turn (question
    index, transcript, STT status, timestamp) instead of appending to a plain
    array, so answers from different questions can never be conflated and the
    final evaluation can read per-turn quality (VALID / LOW_CONFIDENCE ...).

    Returns the FULL session state (409 when the session is already
    completed), so the frontend can resync.
    """
    data = request.get_json() or {}
    session_id = data.get('session_id') or data.get('sessionId')
    user_id = data.get('user_id') or data.get('studentId')

    session = _find_interview_session(session_id, user_id)
    if not session:
        # Ownership mismatch (user_id differs) or stale/foreign session id.
        print(f"[INTERVIEW] answer rejected: session {session_id!r} not found "
              f"for user {user_id!r}")
        return jsonify({"error": "Interview session not found"}), 404
    if session.get("status") != "in_progress":
        return jsonify({"error": "Interview session is already completed."}), 409

    answer = (data.get('answer') or '').strip()
    question_index = data.get('question_index')
    if question_index is None:
        question_index = data.get('questionIndex')
    if question_index is None:
        # Fall back to the count of already-saved turns.
        question_index = len(session.get("answer_turns") or session.get("answers") or [])
    try:
        question_index = int(question_index)
    except (TypeError, ValueError):
        question_index = len(session.get("answer_turns") or session.get("answers") or [])

    questions = session.get("questions") or []
    question_text = (questions[question_index]
                     if 0 <= question_index < len(questions) else None)

    turn = {
        "question_index": question_index,
        "question": question_text,
        "transcript": answer,
        # STT quality from /gd/transcribe when the frontend provides it
        # (VALID / LOW_CONFIDENCE / NO_SPEECH / INVALID). Text mode omits it.
        "transcript_status": (data.get('transcript_status') or None),
        "saved_at": datetime.utcnow(),
    }

    # Upsert by question index: retrying a turn (or a double-click) updates
    # that question's turn instead of duplicating/clobbering another one.
    try:
        submissions_collection.update_one(
            {"_id": session["_id"]},
            {"$pull": {"answer_turns": {"question_index": question_index}}},
        )
        submissions_collection.update_one(
            {"_id": session["_id"]},
            {"$push": {"answer_turns": turn}},
        )
    except Exception as exc:
        print(f"[INTERVIEW] answer save failed: {exc}")
        return jsonify({"error": "Could not save the answer."}), 500

    # Keep the legacy plain `answers` array in sync (ordered by question index)
    # for existing consumers; pad missing slots with empty strings so indexes
    # always line up with the questions. Trailing empty slots are trimmed so
    # currentQuestionIndex (= len(answers)) reflects the next UNANSWERED
    # question, not the full deck.
    updated = submissions_collection.find_one({"_id": session["_id"]})
    turns = updated.get("answer_turns") or []
    ordered = [''] * max(len(questions), 1)
    for t in turns:
        idx = t.get("question_index")
        if isinstance(idx, int) and 0 <= idx < len(ordered):
            ordered[idx] = t.get("transcript") or ''
    while ordered and ordered[-1] == '':
        ordered.pop()
    submissions_collection.update_one(
        {"_id": session["_id"]}, {"$set": {"answers": ordered}})

    updated = submissions_collection.find_one({"_id": session["_id"]})
    print(f"[INTERVIEW] answer saved: session={session_id} q={question_index} "
          f"status={turn['transcript_status'] or 'text'} chars={len(answer)}")
    return jsonify({"success": True, "session": _serialize_interview_session(updated)}), 200


@interview_bp.route('/evaluate', methods=['POST'])
def evaluate_answers():
    """Evaluates the candidate performance based on their interview answers.

    Scoring is EVIDENCE-BASED (interview_service.evaluate_interview):
    - every criterion score is derived from the actual transcript text
    - topic relevance is checked per question (RELEVANT / PARTIALLY_RELEVANT /
      IRRELEVANT / NO_ANSWER) and gates the content score
    - empty/unrelated answers can never produce a high score
    - the final score is the mean of per-turn weighted contributions
      (criterion score x weight%), rounded to 2 decimals
    The LLM prompt is gone: the previous flow silently fell back to a fixed
    base-65 score that gave "69% / strong enthusiasm" for empty answers.
    """
    data = request.get_json() or {}
    user_id = data.get('user_id') or data.get('studentId')
    session_id = data.get('session_id') or data.get('sessionId')
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

    # The SAVED session is the source of truth for what was actually said:
    # its answer_turns carry question text + STT status per turn. The request
    # payload is used only for turns the session does not know about.
    session = _find_interview_session(session_id, user_id)
    eval_transcript = []
    saved_turns = (session or {}).get('answer_turns') or []
    saved_by_idx = {t.get('question_index'): t for t in saved_turns
                    if isinstance(t.get('question_index'), int)}

    if saved_turns:
        session_questions = (session or {}).get('questions') or questions
        for idx, q in enumerate(session_questions):
            saved = saved_by_idx.get(idx)
            answer = (saved or {}).get('transcript')
            if answer is None and idx < len(answers):
                answer = answers[idx]
            eval_transcript.append({
                'question': (saved or {}).get('question') or q,
                'answer': answer or '',
                'transcript_status': (saved or {}).get('transcript_status'),
            })
        use_questions = session_questions
    else:
        # No saved turns (e.g. legacy session): evaluate the request payload,
        # which the frontend builds from the actual user answers.
        for item in transcript:
            eval_transcript.append({
                'question': item.get('question', ''),
                'answer': item.get('answer', ''),
                'transcript_status': item.get('transcript_status')
                                     or item.get('status'),
            })
        use_questions = questions

    result = evaluate_interview(eval_transcript, questions=use_questions)

    interview_score = result['score']
    interview_status = result.get('status') or ('PASS' if result.get('passed') else 'FAIL')

    print(f"[INTERVIEW] Evaluation completed (session={session_id}, "
          f"method={result.get('evaluation_method')})")
    print(f"[INTERVIEW] Final score: {interview_score}")
    print(f"[INTERVIEW] Final status: {interview_status}")

    now = datetime.utcnow()
    if session:
        if session.get("status") == "completed":
            # Idempotent re-finalize: return the stored result, never re-score.
            stored = session.get("result") or result
            response = dict(stored)
            response["sessionId"] = str(session["_id"])
            response["session"] = _serialize_interview_session(session)
            return jsonify(response), 200
        submissions_collection.update_one(
            {"_id": session["_id"]},
            {"$set": {
                "status": "completed",
                "result": result,
                "score": interview_score,
                "interview_status": interview_status,
                "completed_at": now,
            }}
        )
        print(f"[INTERVIEW] Result saved: success (session={session_id})")

    # Update the student's stored score only for a matched, valid user.
    if user_id and ObjectId.is_valid(user_id):
        update_res = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "interviewScore": interview_score,
                "interviewStatus": interview_status,
            }}
        )
        print(f"[INTERVIEW] Result saved: "
              f"{'success' if update_res.modified_count else 'user_not_found'} "
              f"(user_id={user_id})")

    response = dict(result)
    if session:
        response["sessionId"] = str(session["_id"])
        refreshed = submissions_collection.find_one({"_id": session["_id"]})
        response["session"] = _serialize_interview_session(refreshed)

    return jsonify(response), 200