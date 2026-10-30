"""
Skill Card System API - student, admin and faculty endpoints.

Security model:
- Every route verifies the JWT. Students may ONLY read/act on their own
  student_id (someone-else's token cannot read another student's data).
- Admin-only routes (config, topics CRUD) check role == 'admin'.
- Faculty/teacher routes check role in ('admin', 'teacher').
- All XP/completion/badge decisions are computed SERVER-SIDE; the frontend
  never submits totals, marks or solved flags.
"""

import base64
import csv
import datetime
import io
from bson import ObjectId
from flask import Blueprint, jsonify, request

from ..database import (
    skill_topics_collection,
    skill_topic_assignments_collection,
    skill_lessons_collection,
    skill_lesson_progress_collection,
    skill_problems_collection,
    skill_submissions_collection,
    skill_assessments_collection,
    skill_assessment_attempts_collection,
    skill_audit_log_collection,
)
from ..services import skill_progress as progress
from ..services import skill_rewards as rewards
from ..services import skill_state
from ..services.skill_seed import ensure_default_content
from ..services.lambda_service import execute_python_code_lambda
from .auth_routes import verify_jwt_token

skill_bp = Blueprint('skill_bp', __name__, url_prefix='/api/skills')


# --------------------------------------------------------------- helpers --
def _auth():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    return verify_jwt_token(token)


def _oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def _deny(message, status=403):
    return jsonify({"success": False, "message": message}), status


def require_role(roles):
    """Decorator verifying JWT presence and allowed role."""
    def wrapper(fn):
        def inner(*args, **kwargs):
            payload = _auth()
            if not payload:
                return _deny("Unauthorized - login required", 401)
            request.jwt_payload = payload
            if roles and payload.get('role') not in roles:
                return _deny("You do not have permission for this action", 403)
            return fn(*args, **kwargs)
        inner.__name__ = fn.__name__
        return inner
    return wrapper


def _actor():
    return {"id": request.jwt_payload["user_id"], "role": request.jwt_payload["role"]}


def _ensure_seeded():
    try:
        ensure_default_content()
    except Exception as exc:
        print(f"[skills] seed skipped: {exc}")


def _assign_badges_once(student_id, topic_obj_id, completion_pct):
    """Grant every progress-badge threshold reached for this topic."""
    granted = []
    for level in progress.PROGRESS_BADGES:
        if completion_pct >= level["min"]:
            res = rewards.grant_progress_badge(
                str(student_id), str(topic_obj_id), level["key"], level["label"],
                completion_pct)
            if res["awarded"]:
                granted.append(level["label"])
    return granted


def _check_topic_completion_bonus(student_id, topic_id, card):
    """100 XP once, when all required activities are complete."""
    counts = card["counts"]
    done = (counts["problems_required"] == 0 or
            counts["problems_solved"] >= counts["problems_required"]) and \
           (counts["lessons_required"] == 0 or
            counts["lessons_completed"] >= counts["lessons_required"]) and \
           (counts["assessments_required"] == 0 or
            counts["assessments_completed"] >= counts["assessments_required"])
    if not done:
        return None
    config = rewards.get_xp_config()
    if counts["problems_required"] and counts["lessons_required"] and counts["assessments_required"]:
        pass
    res = rewards.award_xp(
        student_id, topic_id,
        f"Topic complete bonus", config["topic_complete_bonus"],
        f"topic:{topic_id}:complete", "bonus:topic_complete",
        activity_ref=topic_id,
        description="All required activities completed in this topic "
                    f"(+{config['topic_complete_bonus']} XP)")
    if res["awarded"]:
        return res["xp"]
    return None


def _recompute_and_award(student_id, topic_obj_id):
    """Shared tail of every progress mutation: rebuild card, award badges."""
    topic = skill_topics_collection.find_one({"_id": topic_obj_id})
    card = skill_state.build_card(student_id, topic)
    _assign_badges_once(student_id, topic_obj_id, card["completion_pct"])
    bonuses = _check_topic_completion_bonus(student_id, str(topic_obj_id), card)
    # Proficiency badge (Skill Master) - separate metric.
    if card["proficiency"]["earned"]:
        res = rewards.grant_proficiency_badge(
            student_id, str(topic_obj_id),
            card["proficiency"]["key"], "Skill Master")
        if res["awarded"]:
            granted = None
    return card, bonuses


# ============================================================== STUDENT ==
@skill_bp.route('/me/dashboard', methods=['GET'])
@require_role(('student',))
def student_dashboard():
    student_id = request.jwt_payload["user_id"]
    _ensure_seeded()
    _sync_assignments(student_id)
    data = skill_state.dashboard(student_id)
    return jsonify({"success": True, **data}), 200


def _sync_assignments(student_id):
    """Auto-create DP progress rows? No-op placeholder kept intentionally:
    assignment docs (admin -> student) gate topic visibility only; nothing
    per-topic is pre-created so cards reflect REAL activity only."""
    return True


@skill_bp.route('/topics/<topic_id>', methods=['GET'])
@require_role(('student', 'teacher', 'admin'))
def topic_detail(topic_id):
    if not _oid(topic_id):
        return _deny("Invalid topic id", 400)
    request_page = request.args.get('as_student')
    student_id = request.jwt_payload["user_id"]
    if request.jwt_payload["role"] == 'student':
        student_id = student_id
    elif request_page:
        student_id = request_page
    _ensure_seeded()
    data = skill_state.topic_detail(student_id, topic_id)
    if not data:
        return _deny("Topic not found", 404)
    return jsonify({"success": True, **data}), 200


# ----------------------------------------------------------- lessons ---
@skill_bp.route('/lessons/<lesson_id>/complete', methods=['POST'])
@require_role(('student',))
def complete_lesson(lesson_id):
    lesson_oid = _oid(lesson_id)
    if not lesson_oid:
        return _deny("Invalid lesson id", 400)
    lesson = skill_lessons_collection.find_one({"_id": lesson_oid})
    if not lesson:
        return _deny("Lesson not found", 404)

    student_id = request.jwt_payload["user_id"]
    topic_id = str(lesson["topic_id"])

    # Idempotent completion - unique (student, lesson) index backs this up.
    if skill_lesson_progress_collection.find_one(
            {"student_id": student_id, "lesson_id": lesson_id}):
        card, _ = _recompute_and_award(student_id, lesson["topic_id"])
        return jsonify({"success": True, "duplicate": True,
                        "message": "Lesson already completed", "card": card}), 200

    try:
        skill_lesson_progress_collection.insert_one({
            "student_id": student_id,
            "topic_id": topic_id,
            "lesson_id": lesson_id,
            "required": True,
            "at": datetime.datetime.utcnow(),
        })
    except Exception as exc:  # unique index lost the race
        if "duplicate key" in str(exc).lower() or "E11000" in str(exc):
            card, _ = _recompute_and_award(student_id, lesson["topic_id"])
            return jsonify({"success": True, "duplicate": True,
                            "card": card}), 200
        raise

    config = rewards.get_xp_config()
    xp_result = rewards.award_xp(
        student_id, topic_id, "Completed lesson: " + lesson["title"],
        config["lesson_complete"], f"lesson:{lesson_id}", "lesson", lesson_id)
    card, bonus = _recompute_and_award(student_id, lesson["topic_id"])
    return jsonify({"success": True, "duplicate": False, "xp_awarded": xp_result["xp"],
                    "total_xp": xp_result["total_xp"],
                    "topic_bonus_awarded": bonus, "card": card}), 200


# --------------------------------------------------- coding practice ---
def _evaluate_submission(problem, source_code):
    """Run source against every test case through the REAL execution engine.

    Success is decided here on the server - never by the frontend.
    """
    results = []
    passed_count = 0
    statuses_ok = {3}          # Judge0 Accepted
    for case in problem.get("test_cases", []):
        outcome = execute_python_code_lambda(source_code, case["input"])
        stdout = ""
        stderr = ""
        try:
            if outcome.get("stdout"):
                stdout = base64.b64decode(outcome["stdout"]).decode("utf-8", "replace")
            if outcome.get("stderr"):
                stderr = base64.b64decode(outcome["stderr"]).decode("utf-8", "replace")
        except Exception:
            pass
        status_id = (outcome.get("status") or {}).get("id")
        ok = status_id in statuses_ok and stdout.strip() == case["expectedOutput"].strip()
        results.append({
            "input": case["input"],
            "expected": case["expectedOutput"],
            "actual": stdout.strip(),
            "error": stderr or (outcome.get("status") or {}).get("description", "Execution failed"),
            "passed": ok,
        })
        if ok:
            passed_count += 1
    total = len(problem.get("test_cases", [])) or 1
    return passed_count == total, results


@skill_bp.route('/problems/<problem_id>/submit', methods=['POST'])
@require_role(('student',))
def submit_problem(problem_id):
    problem_oid = _oid(problem_id)
    if not problem_oid:
        return _deny("Invalid problem id", 400)
    problem = skill_problems_collection.find_one({"_id": problem_oid})
    if not problem:
        return _deny("Problem not found", 404)

    data = request.get_json() or {}
    source_code = data.get("code")
    if not source_code:
        return _deny("Code is required", 400)

    student_id = request.jwt_payload["user_id"]
    topic_id = problem["topic_id"]

    all_passed, case_results = _evaluate_submission(problem, source_code)
    attempt_no = skill_submissions_collection.count_documents(
        {"student_id": student_id, "problem_id": str(problem_oid)}) + 1
    skill_submissions_collection.insert_one({
        "student_id": student_id,
        "topic_id": str(topic_id),
        "problem_id": str(problem_oid),
        "attempt_no": attempt_no,
        "code": source_code,
        "cases": case_results,
        "all_passed": all_passed,
        # solved_credit appears in exactly ONE document per (student, problem)
        "solved_credit": False,
        "status": "solved" if all_passed else "failed",
        "at": datetime.datetime.utcnow(),
    })

    response = {"success": True, "solved": False, "case_results": case_results,
                "attempt_no": attempt_no}
    if not all_passed:
        # Failed attempts are recorded for analytics but earn NOTHING.
        return jsonify(response), 200

    # Mark the single solved-credit doc.
    if not skill_submissions_collection.find_one(
            {"student_id": student_id, "problem_id": str(problem_oid),
             "solved_credit": True}):
        skill_submissions_collection.update_one(
            {"student_id": student_id, "problem_id": str(problem_oid)},
            {"$set": {"solved_credit": True}})
        config = rewards.get_xp_config()
        xp = rewards.problem_difficulty_xp(problem.get("difficulty"), config)
        xp_result = rewards.award_xp(
            student_id, str(topic_id),
            f"Solved problem: {problem['title']}", xp,
            f"problem:{problem_oid}:pass", "problem", str(problem_oid))
        response.update({
            "solved": True,
            "xp_awarded": 0 if xp_result["duplicate"] else xp_result["xp"],
            "total_xp": xp_result["total_xp"],
        })
        card, bonus = _recompute_and_award(student_id, topic_id)
        if bonus:
            response["topic_bonus_awarded"] = bonus
            response["total_xp"] = (response.get("total_xp") or 0) + bonus
        response["card"] = card
    return jsonify(response), 200


# ------------------------------------------------------- assessments ----
@skill_bp.route('/assessments/<assessment_id>', methods=['GET'])
@require_role(('student',))
def get_assessment(assessment_id):
    oid = _oid(assessment_id)
    assessment = skill_assessments_collection.find_one({"_id": oid}) if oid else None
    if not assessment:
        return _deny("Assessment not found", 404)
    student_id = request.jwt_payload["user_id"]
    attempts = list(skill_assessment_attempts_collection.find(
        {"student_id": student_id, "assessment_id": assessment_id}
    ).sort("attempt_no", 1))
    if len(attempts) > assessment.get("retakes_allowed", 0):
        return _deny("Retake limit reached for this assessment", 409)
    # Questions WITHOUT answers - grading happens on the server.
    return jsonify({
        "success": True,
        "assessment": {
            "id": assessment_id, "title": assessment["title"],
            "max_marks": assessment["max_marks"],
            "pass_pct": assessment.get("pass_pct", 40),
            "retakes_allowed": assessment.get("retakes_allowed", 0),
            "questions": [{"question": q["question"], "options": q["options"],
                           "marks": q.get("marks", 1)}
                          for q in assessment["questions"]],
            "attempts_done": len(attempts),
        }
    }), 200


@skill_bp.route('/assessments/<assessment_id>/submit', methods=['POST'])
@require_role(('student',))
def submit_assessment(assessment_id):
    oid = _oid(assessment_id)
    assessment = skill_assessments_collection.find_one({"_id": oid}) if oid else None
    if not assessment:
        return _deny("Assessment not found", 404)

    student_id = request.jwt_payload["user_id"]
    topic_id = assessment["topic_id"]
    existing_attempts = list(skill_assessment_attempts_collection.find(
        {"student_id": student_id, "assessment_id": assessment_id}
    ).sort("attempt_no", 1))
    if len(existing_attempts) > assessment.get("retakes_allowed", 0):
        return _deny("Retake limit reached for this assessment", 409)

    answers = (request.get_json() or {}).get("answers") or {}
    marks = 0
    for idx, question in enumerate(assessment["questions"]):
        if str(idx) in answers and answers[str(idx)] == question["answer"]:
            marks += question.get("marks", 1)
    max_marks = assessment["max_marks"] or sum(q.get("marks", 1) for q in assessment["questions"])
    pct = round(marks / max_marks * 100, 1) if max_marks else 0
    pass_score = assessment.get("pass_pct", 40)
    is_pass = pct >= pass_score

    attempt_no = len(existing_attempts) + 1
    try:
        skill_assessment_attempts_collection.insert_one({
            "student_id": student_id, "topic_id": str(topic_id),
            "assessment_id": assessment_id, "attempt_no": attempt_no,
            "marks": marks, "max_marks": max_marks, "pct": pct,
            "pass": is_pass, "completed": True,
            "at": datetime.datetime.utcnow(),
        })
    except Exception as exc:  # duplicate attempt race (double tap)
        if "duplicate key" in str(exc).lower() or "E11000" in str(exc):
            return jsonify({"success": True, "duplicate": True,
                            "message": "Attempt already recorded"}), 200
        raise

    config = rewards.get_xp_config()
    total_xp = rewards.topic_total_xp(student_id, str(topic_id))
    xp_gained = 0
    if is_pass:
        pass_xp, _ = rewards.assessment_pass_xp(pct, is_pass, pass_score, config)
        result = rewards.award_xp(
            student_id, str(topic_id),
            f"Passed assessment: {assessment['title']}", pass_xp,
            f"assessment:{assessment_id}:pass", "assessment", assessment_id,
            description=f"Assessment {assessment['title']} passed at {pct}% (+{pass_xp} XP)")
        if result["awarded"]:
            xp_gained += result["xp"]
            total_xp = result["total_xp"]
    if pct >= config["high_score_threshold"]:
        bonus_result = rewards.award_xp(
            student_id, str(topic_id),
            f"Score 90%+ bonus: {assessment['title']}",
            config["assessment_high_score_bonus"],
            f"assessment:{assessment_id}:highscore", "bonus:high_score",
            assessment_id)
        if bonus_result["awarded"]:
            xp_gained += bonus_result["xp"]
            total_xp = bonus_result["total_xp"]

    card, bonus = _recompute_and_award(student_id, topic_id)
    payload = {
        "success": True, "marks": marks, "max_marks": max_marks, "pct": pct,
        "pass": is_pass, "pass_pct": pass_score, "attempt_no": attempt_no,
        "xp_awarded": xp_gained, "total_xp": total_xp, "card": card,
    }
    if bonus:
        payload["topic_bonus_awarded"] = bonus
        payload["total_xp"] = payload["total_xp"] + bonus
    return jsonify(payload), 200


# ============================================================== TEACHER ==
@skill_bp.route('/teacher/progress', methods=['GET'])
@require_role(('teacher', 'admin'))
def teacher_progress():
    """Batch / per-student progress with filters; shows sensitive totals
    only for roles allowed to review them."""
    from ..database import users_collection
    _ensure_seeded()

    topic_filter = (request.args.get('topic') or '').strip()
    min_pct = request.args.get('min_pct', type=float)
    max_pct = request.args.get('max_pct', type=float)
    inactive_days = request.args.get('inactive_days', type=int)

    students = list(users_collection.find({"role": "student"}))
    rows = []
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=inactive_days or 0)
              if inactive_days else None)
    for student in students:
        sid = str(student["_id"])
        cards = [c for c in (skill_state.build_card(sid, t)
                             for t in skill_state.list_topics()) if c]
        if topic_filter:
            cards = [c for c in cards if c["topic"]["name"].lower() == topic_filter.lower()]
        if not cards:
            continue
        avg_pct = round(sum(c["completion_pct"] for c in cards) / len(cards), 1)
        if min_pct is not None and avg_pct < min_pct:
            continue
        if max_pct is not None and avg_pct > max_pct:
            continue
        last_activity = max((c["last_activity"] for c in cards
                             if c["last_activity"]), default=None)
        if cutoff and (not last_activity or last_activity < cutoff):
            continue
        needs_support = avg_pct < 25 or (inactive_days and (
            not last_activity or
            last_activity < datetime.datetime.utcnow() - datetime.timedelta(days=inactive_days)))
        rows.append({
            "student_id": sid, "name": student.get("name", ""),
            "department": student.get("department", ""),
            "avg_completion_pct": avg_pct, "total_xp": rewards._total_xp(sid),
            "problems_solved": sum(c["counts"]["problems_solved"] for c in cards),
            "lessons_completed": sum(c["counts"]["lessons_completed"] for c in cards),
            "assessments_passed": sum(c["counts"]["assessments_passed"] for c in cards),
            "last_activity": last_activity,
            "needs_support": needs_support,
            "cards": [{"topic": c["topic"]["name"], "pct": c["completion_pct"],
                       "badge": c["badge_label"]} for c in cards],
        })
    rows.sort(key=lambda r: -r["avg_completion_pct"])
    return jsonify({"success": True, "students": rows, "count": len(rows)}), 200


@skill_bp.route('/teacher/export', methods=['GET'])
@require_role(('teacher', 'admin'))
def teacher_export():
    """CSV export of batch progress (Excel-compatible)."""
    from ..database import users_collection
    students = list(users_collection.find({"role": "student"}))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Department", "Avg Completion %", "XP",
                     "Problems Solved", "Lessons Completed",
                     "Assessments Passed", "Last Activity", "Needs Support"])
    for student in students:
        sid = str(student["_id"])
        cards = [c for c in (skill_state.build_card(sid, t)
                             for t in skill_state.list_topics()) if c]
        if not cards:
            continue
        last = max((c["last_activity"] for c in cards if c["last_activity"]),
                   default=None)
        writer.writerow([
            student.get("name", ""), student.get("department", ""),
            round(sum(c["completion_pct"] for c in cards) / len(cards), 1),
            rewards._total_xp(sid),
            sum(c["counts"]["problems_solved"] for c in cards),
            sum(c["counts"]["lessons_completed"] for c in cards),
            sum(c["counts"]["assessments_passed"] for c in cards),
            last.isoformat() if last else "",
            "yes" if sum(c["completion_pct"] for c in cards) / len(cards) < 25 else "no",
        ])
    csv_bytes = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    csv_bytes.seek(0)
    from flask import Response
    response = Response(csv_bytes, mimetype="text/csv")
    response.headers["Content-Disposition"] = \
        f"attachment; filename=skill_progress_{datetime.date.today()}.csv"
    return response


# ================================================================ ADMIN ==
@skill_bp.route('/admin/config', methods=['GET'])
@require_role(('admin',))
def admin_get_config():
    return jsonify({
        "success": True,
        "xp": rewards.get_xp_config(),
        "badges": rewards.get_badge_rules() or {
            "progress": progress.PROGRESS_BADGES,
            "proficiency": progress.DEFAULT_PROFICIENCY_RULE,
        },
    }), 200


@skill_bp.route('/admin/config/xp', methods=['PUT'])
@require_role(('admin',))
def admin_update_xp():
    try:
        merged = rewards.update_xp_config(request.get_json() or {}, _actor())
        return jsonify({"success": True, "xp": merged}), 200
    except ValueError as exc:
        return _deny(str(exc), 400)


@skill_bp.route('/admin/badges', methods=['PUT'])
@require_role(('admin',))
def admin_update_badges():
    try:
        rules = rewards.update_badge_rules(request.get_json() or {}, _actor())
        return jsonify({"success": True, "badges": rules}), 200
    except ValueError as exc:
        return _deny(str(exc), 400)


@skill_bp.route('/admin/audit', methods=['GET'])
@require_role(('admin',))
def admin_audit():
    docs = list(skill_audit_log_collection.find().sort("at", -1).limit(200))
    return jsonify({"success": True, "audit": [{
        "id": str(d["_id"]), "action": d["action"], "actor_id": d.get("actor_id"),
        "actor_role": d.get("actor_role"), "details": d.get("details"),
        "at": d.get("at"),
    } for d in docs]}), 200


@skill_bp.route('/admin/topics', methods=['POST'])
@require_role(('admin',))
def admin_create_topic():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _deny("Topic name is required", 400)
    if skill_topics_collection.find_one({"name": name}):
        return _deny("A topic with that name already exists", 409)
    order = skill_topics_collection.count_documents({})
    result = skill_topics_collection.insert_one({
        "name": name, "icon": data.get("icon", "book"),
        "description": data.get("description", ""), "order": order,
        "archived": False, "source": "admin",
        "createdAt": datetime.datetime.utcnow(),
    })
    rewards.audit("topic_created", _actor(),
                  {"topic_id": str(result.inserted_id), "name": name})
    return jsonify({"success": True, "id": str(result.inserted_id)}), 201


@skill_bp.route('/admin/topics/<topic_id>', methods=['PUT'])
@require_role(('admin',))
def admin_update_topic(topic_id):
    oid = _oid(topic_id)
    if not oid:
        return _deny("Invalid topic id", 400)
    updates = {}
    data = request.get_json() or {}
    for field in ("name", "description", "icon", "archived"):
        if field in data:
            updates[field] = data[field]
    if not updates:
        return _deny("No valid fields to update", 400)
    skill_topics_collection.update_one({"_id": oid}, {"$set": updates})
    rewards.audit("topic_updated", _actor(), {"topic_id": topic_id, "fields": list(updates)})
    return jsonify({"success": True}), 200


@skill_bp.route('/admin/topics/<topic_id>/lessons', methods=['POST'])
@require_role(('admin',))
def admin_add_lesson(topic_id):
    oid = _oid(topic_id)
    if not oid:
        return _deny("Invalid topic id", 400)
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return _deny("Lesson title is required", 400)
    order = skill_lessons_collection.count_documents({"topic_id": oid})
    skill_lessons_collection.insert_one({
        "topic_id": oid, "title": title,
        "content": data.get("content", ""), "required": True, "order": order,
        "source": "admin",
    })
    rewards.audit("lesson_created", _actor(), {"topic_id": topic_id, "title": title})
    return jsonify({"success": True}), 201


@skill_bp.route('/admin/topics/<topic_id>/problems', methods=['POST'])
@require_role(('admin',))
def admin_add_problem(topic_id):
    oid = _oid(topic_id)
    if not oid:
        return _deny("Invalid topic id", 400)
    data = request.get_json() or {}
    if not (data.get("title") or "").strip():
        return _deny("Problem title is required", 400)
    cases = [{"input": c.get("input", ""), "expectedOutput": c.get("expectedOutput", "")}
             for c in (data.get("test_cases") or [])]
    if not cases:
        cases = [{"input": "", "expectedOutput": ""}]
    skill_problems_collection.insert_one({
        "topic_id": oid, "title": data["title"],
        "difficulty": data.get("difficulty", "easy"),
        "description": data.get("description", ""),
        "starter_code": data.get("starter_code", ""),
        "required": True, "test_cases": cases, "source": "admin",
    })
    rewards.audit("problem_created", _actor(),
                  {"topic_id": topic_id, "title": data["title"],
                   "difficulty": data.get("difficulty", "easy")})
    return jsonify({"success": True}), 201


@skill_bp.route('/admin/topics/<topic_id>/assessments', methods=['POST'])
@require_role(('admin',))
def admin_add_assessment(topic_id):
    oid = _oid(topic_id)
    if not oid:
        return _deny("Invalid topic id", 400)
    data = request.get_json() or {}
    if not (data.get("title") or "").strip():
        return _deny("Assessment title is required", 400)
    questions = [{
        "question": q.get("question", ""), "options": q.get("options", []),
        "answer": int(q.get("answer", 0)), "marks": int(q.get("marks", 1)),
    } for q in (data.get("questions") or [])]
    if not questions:
        return _deny("At least one question is required", 400)
    skill_assessments_collection.insert_one({
        "topic_id": oid, "title": data["title"],
        "max_marks": sum(q["marks"] for q in questions) or data.get("max_marks", 20),
        "pass_pct": int(data.get("pass_pct", 40)),
        "required": True,
        "retakes_allowed": int(data.get("retakes_allowed", 2)),
        "questions": questions, "source": "admin",
    })
    rewards.audit("assessment_created", _actor(),
                  {"topic_id": topic_id, "title": data["title"]})
    return jsonify({"success": True}), 201


@skill_bp.route('/admin/assign', methods=['POST'])
@require_role(('admin',))
def admin_assign_topic():
    data = request.get_json() or {}
    topic_id = _oid(data.get("topic_id"))
    student_ids = data.get("student_ids") or []
    if not topic_id or not student_ids:
        return _deny("topic_id and student_ids are required", 400)
    assigned = 0
    for sid in student_ids:
        try:
            skill_topic_assignments_collection.insert_one({
                "topic_id": topic_id, "student_id": str(sid),
                "assigned_at": datetime.datetime.utcnow(),
                "assigned_by": _actor()["id"]})
            assigned += 1
        except Exception as exc:
            if "duplicate key" not in str(exc).lower() and "E11000" not in str(exc):
                raise
    rewards.audit("topic_assigned", _actor(),
                  {"topic_id": str(topic_id), "students": assigned})
    return jsonify({"success": True, "assigned": assigned}), 200
