# lms_portal_backend/app/routes/teacher_routes.py

from flask import Blueprint, request, jsonify
from ..database import users_collection, assignments_collection, teacher_assignments_collection, submissions_collection
from ..models.user import user_helper
from ..services.ai_service import get_ai_response
from ..services.question_bank import pick_questions as pick_bank_questions
from ..services import assessment_state
from bson import ObjectId
import random
import uuid
from datetime import datetime

teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/api/teacher')

# Normal quiz length (dynamic pooling): every attempt is served a randomized
# selection of 10 unique questions drawn from the assignment's bank, never
# the whole static list in the same order every time.
DEFAULT_QUIZ_QUESTIONS = 10
MAX_QUIZ_QUESTIONS = 15


def _clamp_quiz_length(num_questions):
    """Normalize a requested quiz length to the normal 10-15 range."""
    try:
        n = int(num_questions)
    except (TypeError, ValueError):
        return DEFAULT_QUIZ_QUESTIONS
    return max(1, min(n, MAX_QUIZ_QUESTIONS))


def _build_attempt_paper(bank, requested=None):
    """Build one attempt's randomized question paper.

    - Randomly selects the requested number of UNIQUE questions from the
      assignment bank (dynamic randomization per attempt/retake).
    - Small banks are topped up from the master seeded question bank
      (question_bank.py: GK / Grammar / Technical / Logical Reasoning) so a
      10-question paper is always possible even if the stored bank is short.
    - De-duplicates by question text across bank + top-up.
    """
    target = _clamp_quiz_length(requested)
    bank = list(bank or [])
    seen = set()
    for q in bank:
        text = str((q or {}).get("question") or "").strip().lower()
        if text:
            seen.add(text)
    if len(bank) >= target:
        return random.sample(bank, target)

    # Bank smaller than the target: top up from the seeded master bank,
    # excluding anything already present.
    top_up = pick_bank_questions(
        target - len(bank),
        categories=["General Knowledge", "Grammar", "Logical Reasoning"],
    )
    for q in top_up:
        text = str((q or {}).get("question") or "").strip().lower()
        if text and text not in seen:
            seen.add(text)
            bank.append(q)
    return random.sample(bank, len(bank)) if bank else []

@teacher_bp.route('/students/progress', methods=['GET'])
def get_student_progress():
    students = users_collection.find({"role": "student"})
    student_list = []
    
    for student in students:
        student_id = str(student["_id"])
        # Get submission count for this student
        submission_count = submissions_collection.count_documents({"student_id": student_id})
        
        # Update student record with submission count
        users_collection.update_one(
            {"_id": student["_id"]},
            {"$set": {"submittedAssignments": submission_count}}
        )
        
        student_list.append(user_helper(student, submission_count))
    
    return jsonify(student_list)

@teacher_bp.route('/assignments', methods=['POST'])
def create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('dueDate', datetime.now().isoformat())
        assignment_type = data.get('type', 'Assignment')
        quiz_questions = data.get('quizQuestions')
        
        if not all([title, description]):
            return jsonify({"error": "Missing required fields"}), 400
        
        assignment = {
            "title": title,
            "description": description,
            "dueDate": due_date,
            "type": assignment_type,
            "createdBy": "teacher",
            "createdAt": datetime.now().isoformat()
        }
        
        # Store quiz questions directly in the assignment document
        if quiz_questions:
            assignment["quizQuestions"] = quiz_questions
        
        # Save to MongoDB
        result = teacher_assignments_collection.insert_one(assignment)
        assignment_id = str(result.inserted_id)
        
        # Also store in memory for backward compatibility
        if quiz_questions:
            quiz_questions_storage[assignment_id] = quiz_questions
        
        return jsonify({
            "message": "Assignment created successfully",
            "assignment_id": assignment_id
        }), 201
        
    except Exception as e:
        print(f"Error creating assignment: {e}")
        return jsonify({"error": "Failed to create assignment"}), 500

def generate_quiz_questions(title, description):
    try:
        topic = f"{title}. {description}"
        prompt = f"""
        Create a quiz based on this topic: {topic}
        Generate exactly 5 multiple-choice questions.
        IMPORTANT: Your entire response must be a single, raw JSON object.
        The JSON object must have a single key "questions".
        The value of "questions" must be a list of exactly 5 question objects.
        Each question object must have: "question", "options" (list of 4), "correct_answer".
        """
        ai_response = get_ai_response(prompt)
        if ai_response and "questions" in ai_response:
            return ai_response["questions"]
        return None
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        return None

@teacher_bp.route('/assignments', methods=['GET'])
def get_teacher_assignments():
    """Get all assignments created by teachers"""
    try:
        assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        teacher_assignments = []
        for a in assignments:
            teacher_assignments.append({
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "dueDate": a["dueDate"],
                "type": a.get("type", "manual"),
                "createdBy": a["createdBy"],
                "createdAt": a.get("createdAt"),
                "questions": a.get("questions")
            })
        return jsonify(teacher_assignments), 200
    except Exception as e:
        print(f"Error fetching teacher assignments: {e}")
        return jsonify({"error": "Failed to fetch assignments"}), 500

@teacher_bp.route('/assignments/<assignment_id>/questions', methods=['GET'])
def get_quiz_questions(assignment_id):
    try:
        if assignment_id in quiz_questions_storage:
            return jsonify({"questions": quiz_questions_storage[assignment_id]}), 200
        else:
            return jsonify({"error": "Quiz questions not found"}), 404
    except Exception as e:
        print(f"Error fetching quiz questions: {e}")
        return jsonify({"error": "Failed to fetch quiz questions"}), 500

@teacher_bp.route('/admin-assignments/<teacher_id>', methods=['GET'])
def get_admin_assignments(teacher_id):
    try:
        query = {"teacherId": ObjectId(teacher_id), "createdBy": "admin"}
        assignments = list(assignments_collection.find(query))
        results = []
        for a in assignments:
            results.append({
                "id": str(a['_id']),
                "title": a['title'],
                "description": a['description'],
                "status": a.get('status', 'Pending'),
                "dueDate": a.get('dueDate'),
                "createdBy": "admin"
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route('/admin_tasks', methods=['GET'])
def get_admin_tasks():
    """Get tasks assigned by admin to teachers"""
    try:
        # Get all admin-created assignments
        tasks = list(assignments_collection.find({"createdBy": "admin"}))
        admin_tasks = []
        for t in tasks:
            admin_tasks.append({
                "id": str(t["_id"]),
                "title": t["title"],
                "description": t["description"],
                "status": t.get("status", "Pending"),
                "dueDate": t.get("dueDate"),
                "teacherId": str(t.get("teacherId", ""))
            })
        return jsonify(admin_tasks), 200
    except Exception as e:
        print(f"Error fetching admin tasks: {e}")
        return jsonify({"error": "Failed to fetch admin tasks"}), 500

@teacher_bp.route('/admin-assignments/<assignment_id>/complete', methods=['PATCH'])
def mark_assignment_complete(assignment_id):
    try:
        result = assignments_collection.update_one(
            {"_id": ObjectId(assignment_id)},
            {"$set": {"status": "Completed"}}
        )
        if result.modified_count == 1:
            return jsonify({"success": True}), 200
        return jsonify({"error": "Assignment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NEW: Edit Assignment Route ---
@teacher_bp.route('/assignments/<assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """Update an existing assignment"""
    try:
        data = request.get_json()
        
        update_fields = {}
        if 'title' in data:
            update_fields['title'] = data['title']
        if 'description' in data:
            update_fields['description'] = data['description']
        if 'dueDate' in data:
            update_fields['dueDate'] = data['dueDate']
            
        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400
        
        # Update in MongoDB
        result = teacher_assignments_collection.update_one(
            {"_id": ObjectId(assignment_id)},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Assignment not found"}), 404
            
        # Get the updated assignment
        updated_assignment = teacher_assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        assignment_dict = {
            "id": str(updated_assignment["_id"]),
            "title": updated_assignment["title"],
            "description": updated_assignment["description"],
            "dueDate": updated_assignment["dueDate"],
            "type": updated_assignment.get("type", "manual"),
            "createdBy": updated_assignment["createdBy"]
        }
            
        return jsonify({"message": "Assignment updated successfully", "assignment": assignment_dict}), 200
        
    except Exception as e:
        print(f"Error updating assignment: {e}")
        return jsonify({"error": "Failed to update assignment"}), 500

# ------------------------------------------------------------------
# Teacher-Assigned MCQ Assessment: server-controlled lifecycle
# (timer, expiry, tab-switch failure, pass/fail result storage)
# ------------------------------------------------------------------

def _safe_object_id(value):
    """Convert to ObjectId, or None for invalid/foreign-format ids."""
    try:
        return ObjectId(value) if value and ObjectId.is_valid(value) else None
    except (TypeError, ValueError):
        return None

@teacher_bp.route('/assignments/<assignment_id>/assessment/start', methods=['POST'])
def start_quiz_assessment(assignment_id):
    """Start (or resume) a timed MCQ assessment attempt for a student.

    The start/expiry timestamps are SERVER-generated and stored in MongoDB,
    so refreshing or reopening the page can never reset the timer.
    """
    try:
        data = request.get_json() or {}
        student_id = str(data.get('student_id') or '')
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        assignment_oid = _safe_object_id(assignment_id)
        assignment = teacher_assignments_collection.find_one({"_id": assignment_oid}) if assignment_oid else None
        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404

        # DYNAMIC QUESTION POOLING: every attempt (fresh start AND every
        # retake) is served its own randomized paper. The bank from the
        # assignment is shuffled and trimmed to the normal test length
        # (10-15 questions) so no two attempts see the same paper in the
        # same order - the old behavior replayed the identical stored list
        # every time (static repetition).
        # Note: assignment banks built from the categorized question bank
        # already carry a 'category' tag per question (Grammar / General
        # Knowledge / Technical / Logical Reasoning); the tag travels with
        # each question into the attempt snapshot and the answer review.
        bank = assignment.get("quizQuestions") or []
        questions = _build_attempt_paper(bank, data.get('num_questions'))

        # RETAKE FLOW: an explicit retake archives the finished attempt
        # (kept for history with its score) and creates a fresh attempt.
        # Without retake=True a finished attempt is still returned locked.
        retake = bool(data.get('retake'))

        attempt_key = f"{assignment_id}_{student_id}"
        attempt, created = assessment_state.start_assessment(
            assessment_state.TYPE_TEACHER_QUIZ,
            attempt_key,
            assessment_state.QUIZ_DURATION_MINUTES,
            total_questions=len(questions),
            meta={"assignment_id": assignment_id, "student_id": student_id},
            extra={
                "assignment_id": assignment_id,
                "student_id": student_id,
            },
            retake=retake,
            # Per-attempt snapshot: /status and /submit always use THIS list,
            # never the live assignment list (consistency + retake variety).
            questions=questions,
        )
        status = attempt.get("status")
        active = status == assessment_state.STATUS_IN_PROGRESS

        # Serve the attempt's OWN snapshot (a resumed/legacy attempt gets its
        # consistent list back, not a fresh shuffle).
        served_questions = assessment_state.ensure_attempt_questions(
            attempt, questions)

        return jsonify({
            "success": True,
            "created": created,
            "assessment": {
                "assignmentId": assignment_id,
                "title": assignment.get("title"),
                "durationMinutes": assessment_state.QUIZ_DURATION_MINUTES,
                "serverTime": datetime.utcnow().isoformat(),
            },
            "attempt": assessment_state.serialize_attempt(attempt),
            "active": active,
            "canRetake": not active,
            "questions": served_questions if active else [],
        }), 200
    except Exception as e:
        print(f"Error starting quiz assessment: {e}")
        return jsonify({"error": "Failed to start assessment"}), 500

@teacher_bp.route('/assignments/<assignment_id>/assessment/status', methods=['GET'])
def quiz_assessment_status(assignment_id):
    """Fetch the server-side assessment state (used on refresh/reopen)."""
    try:
        student_id = request.args.get('student_id', '')
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        attempt_key = f"{assignment_id}_{student_id}"
        attempt, active = assessment_state.get_attempt_status(
            assessment_state.TYPE_TEACHER_QUIZ, attempt_key)
        if not attempt:
            return jsonify({
                "success": True,
                "status": assessment_state.STATUS_NOT_STARTED,
                "attempt": None,
                "active": False,
            }), 200

        response = {
            "success": True,
            "status": attempt.get("status"),
            "attempt": assessment_state.serialize_attempt(attempt),
            "active": active,
        }
        # ACTIVE attempt: serve the attempt's OWN per-attempt question
        # snapshot (stored at start), never a fresh shuffle - resuming must
        # show exactly the paper the attempt began with.
        if active:
            assignment_oid = _safe_object_id(assignment_id)
            assignment = teacher_assignments_collection.find_one({"_id": assignment_oid}) if assignment_oid else None
            bank = (assignment or {}).get("quizQuestions") or []
            response["questions"] = assessment_state.ensure_attempt_questions(
                attempt, bank)
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching quiz assessment status: {e}")
        return jsonify({"error": "Failed to fetch assessment status"}), 500

@teacher_bp.route('/assignments/<assignment_id>/assessment/fail', methods=['POST'])
def fail_quiz_assessment(assignment_id):
    """Automatic failure (TAB_SWITCH / TIME_EXPIRED). Server validates that the
    attempt is still active before storing the permanent FAILED result."""
    try:
        data = request.get_json() or {}
        student_id = str(data.get('student_id') or '')
        reason = data.get('reason') or assessment_state.FAILURE_TAB_SWITCH
        if reason not in (assessment_state.FAILURE_TAB_SWITCH, assessment_state.FAILURE_TIME_EXPIRED):
            reason = assessment_state.FAILURE_TAB_SWITCH
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        attempt_key = f"{assignment_id}_{student_id}"
        attempt, active = assessment_state.get_attempt_status(
            assessment_state.TYPE_TEACHER_QUIZ, attempt_key)
        if not attempt:
            return jsonify({"error": "Assessment attempt not found"}), 404

        doc, already_final = assessment_state.fail_assessment(attempt, reason)
        return jsonify({
            "success": True,
            "alreadyFinal": already_final,
            "wasActive": active,
            "attempt": assessment_state.serialize_attempt(doc),
        }), 200
    except Exception as e:
        print(f"Error failing quiz assessment: {e}")
        return jsonify({"error": "Failed to record assessment failure"}), 500

@teacher_bp.route('/assignments/<assignment_id>/assessment/submit', methods=['POST'])
def submit_quiz_assessment(assignment_id):
    """Submit a teacher-assigned MCQ assessment.

    Server validates: attempt exists, is active, not already submitted, and
    the current server time is before expiry. Computes score, determines
    PASS/FAIL (70% pass mark) and stores ONE authoritative result record.
    """
    try:
        data = request.get_json() or {}
        student_id = str(data.get('student_id') or '')
        answers = data.get('answers')
        if not student_id or answers is None:
            return jsonify({"error": "student_id and answers are required"}), 400

        attempt_key = f"{assignment_id}_{student_id}"
        attempt, active = assessment_state.get_attempt_status(
            assessment_state.TYPE_TEACHER_QUIZ, attempt_key)
        if not attempt:
            return jsonify({"error": "Assessment attempt not found"}), 404
        if not active:
            return jsonify({
                "error": "Assessment is no longer active.",
                "status": attempt.get("status"),
                "failureReason": attempt.get("failure_reason"),
                "attempt": assessment_state.serialize_attempt(attempt),
            }), 409

        assignment_oid = _safe_object_id(assignment_id)
        assignment = teacher_assignments_collection.find_one({"_id": assignment_oid}) if assignment_oid else None
        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404
        # The attempt's stored snapshot (not the live assignment bank) is
        # the authority for evaluation - it is exactly what the student saw.
        questions = assessment_state.ensure_attempt_questions(
            attempt, assignment.get("quizQuestions") or [])

        doc, error = assessment_state.evaluate_and_store(attempt, questions, answers)
        if error:
            return jsonify({
                "error": error.get("error", "Submission rejected."),
                "status": error.get("status"),
                "failureReason": doc.get("failure_reason") if doc else None,
                "attempt": assessment_state.serialize_attempt(doc),
            }), 409

        return jsonify({
            "success": True,
            "result": assessment_state.serialize_attempt(doc),
        }), 200
    except Exception as e:
        print(f"Error submitting quiz assessment: {e}")
        return jsonify({"error": "Failed to submit assessment"}), 500

@teacher_bp.route('/submissions', methods=['GET'])
def get_all_submissions():
    """Get all student submissions organized by student"""
    try:
        # Get all students
        students = list(users_collection.find({"role": "student"}))
        
        # Get all teacher assignments
        assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        
        # Get all submissions
        submissions = list(submissions_collection.find())
        
        # Create a lookup for submissions by student_id and assignment_id
        submission_lookup = {}
        for sub in submissions:
            key = f"{sub.get('student_id', '')}_{sub.get('assignment_id', '')}"
            submitted_at = sub.get('submitted_at')
            submission_data = {
                "id": str(sub["_id"]),
                "filename": sub.get("filename", ""),
                "file_path": sub.get("file_path", ""),
                "notes": sub.get("notes", ""),
                "submitted_at": submitted_at.isoformat()
                if isinstance(submitted_at, datetime) else submitted_at
            }
            
            # Include quiz score if available
            if "quiz_score" in sub:
                submission_data["quiz_score"] = sub["quiz_score"]
            if sub.get("status"):
                submission_data["status"] = sub["status"]
            if sub.get("failure_reason"):
                submission_data["failure_reason"] = sub["failure_reason"]
            
            submission_lookup[key] = submission_data
        
        # Build student data with assignment statuses
        student_submissions = []
        for student in students:
            student_id = str(student["_id"])
            student_data = {
                "student_id": student_id,
                "student_name": student["name"],
                "student_email": student.get("email", ""),
                "assignments": []
            }
            
            # Check each assignment for this student
            for assignment in assignments:
                assignment_id = str(assignment["_id"])
                submission_key = f"{student_id}_{assignment_id}"
                
                assignment_status = {
                    "assignment_id": assignment_id,
                    "assignment_title": assignment["title"],
                    "assignment_type": assignment.get("type", "Assignment"),
                    "due_date": assignment.get("dueDate", ""),
                    "submitted": submission_key in submission_lookup,
                    "submission": submission_lookup.get(submission_key)
                }
                
                student_data["assignments"].append(assignment_status)
            
            student_submissions.append(student_data)
        
        return jsonify(student_submissions), 200
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        return jsonify({"error": "Failed to fetch submissions"}), 500