"""
Aggregates a student's persisted progress into topic cards / dashboard data.

Everything comes from the DB: submissions, lesson progress, assessment
attempts, XP transactions. No sample/demo progress is ever fabricated here.
"""

from bson import ObjectId
from ..database import (
    skill_topics_collection,
    skill_topic_assignments_collection,
    skill_lessons_collection,
    skill_lesson_progress_collection,
    skill_problems_collection,
    skill_submissions_collection,
    skill_assessments_collection,
    skill_assessment_attempts_collection,
    skill_activity_history_collection,
)
from . import skill_progress as progress
from . import skill_rewards as rewards


def _oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def list_topics(include_archived=False):
    query = {} if include_archived else {"archived": {"$ne": True}}
    return list(skill_topics_collection.find(query).sort("order", 1))


def topic_by_id(topic_id):
    oid = _oid(topic_id)
    return skill_topics_collection.find_one({"_id": oid}) if oid else None


def compute_topic_state(student_id, topic_id):
    """Raw counts and ratios for one topic from persisted student records."""
    topic_oid = _oid(topic_id)
    if not topic_oid:
        return None
    topic_oid_str = str(topic_oid)

    required_problems = list(skill_problems_collection.find(
        {"topic_id": topic_oid, "required": True}, {"difficulty": 1}))
    problem_ids = {str(p["_id"]) for p in required_problems}
    solved_count = len(list(skill_submissions_collection.find(
        {"student_id": student_id, "topic_id": topic_oid_str,
         "required": True, "solved_credit": True})))
    all_problems_solved = bool(problem_ids) and solved_count >= len(problem_ids)

    total_lessons = skill_lessons_collection.count_documents(
        {"topic_id": topic_oid, "required": True})
    done_lessons = skill_lesson_progress_collection.count_documents(
        {"student_id": student_id, "topic_id": topic_oid_str, "required": True})
    learning_pct = progress.completion_component(done_lessons / total_lessons) if total_lessons else None

    total_assessments = skill_assessments_collection.count_documents(
        {"topic_id": topic_oid, "required": True})
    attempts = list(skill_assessment_attempts_collection.find(
        {"student_id": student_id, "topic_id": topic_oid_str})
        .sort("attempt_no", 1))
    # Completion: distinct assessments with at least one submission.
    done_assessments = len({a["assessment_id"] for a in attempts})
    # Proficiency: best percentage across attempts.
    best_pct = max((a.get("pct") or 0) for a in attempts) if attempts else 0
    passed_assessments = sum(1 for a in attempts if a.get("pass"))

    last_problem_sub = skill_submissions_collection.find_one(
        {"student_id": student_id, "topic_id": topic_oid_str},
        sort=[("at", -1)])
    last_activity = last_problem_sub.get("at") if last_problem_sub else None
    if not last_activity:
        last_attempt = skill_assessment_attempts_collection.find_one(
            {"student_id": student_id, "topic_id": topic_oid_str},
            sort=[("at", -1)])
        last_activity = last_attempt.get("at") if last_attempt else None
    if not last_activity:
        last_lesson = skill_lesson_progress_collection.find_one(
            {"student_id": student_id, "topic_id": topic_oid_str},
            sort=[("at", -1)])
        last_activity = last_lesson.get("at") if last_lesson else None

    state = {
        "category_ratio": {
            "coding": (solved_count / len(problem_ids)) if problem_ids else None,
            "learning": (done_lessons / total_lessons) if total_lessons else None,
            "assessment": (done_assessments / total_assessments) if total_assessments else None,
        },
        "assessment_pct": best_pct,
        "all_problems_solved": all_problems_solved,
        "proficiency_rule": rewards.get_badge_rules().get("proficiency")
        or progress.DEFAULT_PROFICIENCY_RULE,
        "raw": {
            "problems_required": len(problem_ids),
            "problems_solved": solved_count,
            "lessons_required": total_lessons,
            "lessons_completed": done_lessons,
            "assessments_required": total_assessments,
            "assessments_completed": done_assessments,
            "attempts_count": len(attempts),
            "assessments_passed": passed_assessments,
        },
        "last_activity": last_activity,
    }
    return state


def build_card(student_id, topic):
    state = compute_topic_state(student_id, topic["_id"])
    if not state:
        return None
    raw = state["raw"]
    required = {"coding": raw["problems_required"],
                "learning": raw["lessons_required"],
                "assessment": raw["assessments_required"]}
    card = progress.build_topic_card(required, state)
    card.update({
        "topic": {"id": str(topic["_id"]), "name": topic["name"],
                  "icon": topic.get("icon", "book"),
                  "description": topic.get("description", "")},
        "xp": rewards.topic_total_xp(student_id, str(topic["_id"])),
        "last_activity": state["last_activity"],
        "assessment_pct": state.get("assessment_pct", 0),
        "counts": raw,
    })
    return card


def dashboard(student_id):
    topics = list_topics()
    cards = [c for c in (build_card(student_id, t) for t in topics) if c]

    total_xp = rewards._total_xp(student_id)
    badges = list(skill_badge_awards_for_student(student_id))

    solved = sum(c["counts"]["problems_solved"] for c in cards)
    problems = sum(c["counts"]["problems_required"] for c in cards)
    lessons_done = sum(c["counts"]["lessons_completed"] for c in cards)
    lessons_total = sum(c["counts"]["lessons_required"] for c in cards)
    assessments_done = sum(c["counts"]["assessments_completed"] for c in cards)
    assessments_total = sum(c["counts"]["assessments_required"] for c in cards)
    attempts_total = sum(c["counts"]["attempts_count"] for c in cards)
    passed_total = sum(c["counts"]["assessments_passed"] for c in cards)

    attempt_docs = list(skill_assessment_attempts_collection.find(
        {"student_id": student_id}))
    avg_score = (round(sum(a.get("pct") or 0 for a in attempt_docs) / len(attempt_docs), 1)
                 if attempt_docs else 0)

    next_up = None
    if cards:
        started = [c for c in cards if c["completion_pct"] > 0]
        pool = started or cards
        next_up = min(pool, key=lambda c: c["completion_pct"])

    history = list(skill_activity_history_collection.find(
        {"student_id": student_id}).sort("at", -1).limit(8))

    return {
        "totals": {
            "xp": total_xp,
            "badges": len(badges),
            "problems_solved": solved,
            "problems_total": problems,
            "lessons_completed": lessons_done,
            "lessons_total": lessons_total,
            "assessments_completed": assessments_done,
            "assessments_total": assessments_total,
            "attempts": attempts_total,
            "assessments_passed": passed_total,
            "pass_rate": round(passed_total / attempts_total * 100, 1) if attempts_total else 0,
            "average_assessment_score": avg_score,
        },
        "cards": cards,
        "recommended": {
            "topic": next_up["topic"] if next_up else None,
            "completion_pct": next_up["completion_pct"] if next_up else None,
            "next_lesson": next_uncompleted_lesson(student_id, next_up["topic"]["id"]) if next_up else None,
        },
        "recent_activity": [_activity_out(h) for h in history],
        "badges": badges,
    }


def skill_badge_awards_for_student(student_id):
    from ..database import skill_badge_awards_collection
    return [{
        "id": str(d["_id"]), "topic_id": d["topic_id"],
        "badge_key": d["badge_key"], "badge_label": d["badge_label"],
        "completion_pct": d.get("completion_pct"), "at": d.get("at"),
    } for d in skill_badge_awards_collection.find({"student_id": student_id})
        .sort("at", -1)]


def next_uncompleted_lesson(student_id, topic_id):
    topic_oid = _oid(topic_id)
    if not topic_oid:
        return None
    done = {p["lesson_id"] for p in skill_lesson_progress_collection.find(
        {"student_id": student_id, "topic_id": str(topic_oid)})}
    lesson = skill_lessons_collection.find_one(
        {"topic_id": topic_oid, "_id": {"$nin": [_oid(x) for x in done]}},
        sort=[("order", 1)])
    if not lesson:
        return None
    return {"id": str(lesson["_id"]), "title": lesson["title"]}


def topic_detail(student_id, topic_id):
    """All sections/tabs of the topic detail page."""
    topic = topic_by_id(topic_id)
    if not topic:
        return None
    state = compute_topic_state(student_id, topic["_id"])
    if not state:
        return None
    card = build_card(student_id, topic)

    topic_oid = topic["_id"]
    topic_oid_str = str(topic_oid)

    done_lesson_ids = {p["lesson_id"] for p in
                       skill_lesson_progress_collection.find(
                           {"student_id": student_id, "topic_id": topic_oid_str})}
    lessons = [{
        "id": str(l["_id"]), "title": l["title"], "content": l.get("content", ""),
        "order": l.get("order", 0), "completed": str(l["_id"]) in done_lesson_ids,
    } for l in skill_lessons_collection.find({"topic_id": topic_oid}).sort("order", 1)]

    submitted = {s["problem_id"]: s for s in skill_submissions_collection.find(
        {"student_id": student_id, "topic_id": topic_oid_str})}
    problems = [{
        "id": str(p["_id"]), "title": p["title"], "difficulty": p.get("difficulty", "easy"),
        "description": p.get("description", ""), "starter_code": p.get("starter_code", ""),
        "test_case_count": len(p.get("test_cases", [])),
        "solved": str(p["_id"]) in submitted, "required": p.get("required", True),
    } for p in skill_problems_collection.find({"topic_id": topic_oid})]

    attempts_by_assessment = {}
    for a in skill_assessment_attempts_collection.find(
            {"student_id": student_id, "topic_id": topic_oid_str}).sort("attempt_no", 1):
        attempts_by_assessment.setdefault(a["assessment_id"], []).append({
            "attempt_no": a["attempt_no"], "marks": a.get("marks"), "max_marks": a.get("max_marks"),
            "pct": a.get("pct"), "pass": a.get("pass"), "at": a.get("at")})
    assessments = [{
        "id": str(a["_id"]), "title": a["title"], "max_marks": a.get("max_marks"),
        "pass_pct": a.get("pass_pct", 40), "required": a.get("required", True),
        "retakes_allowed": a.get("retakes_allowed", 0),
        "attempts": attempts_by_assessment.get(str(a["_id"]), []),
    } for a in skill_assessments_collection.find({"topic_id": topic_oid})]

    history = list(skill_activity_history_collection.find(
        {"student_id": student_id, "topic_id": topic_oid_str}).sort("at", -1).limit(50))

    earned_badges = [b for b in skill_badge_awards_for_student(student_id)
                     if b["topic_id"] == topic_oid_str]

    return {
        "topic": card["topic"],
        "card": card,
        "lessons": lessons,
        "problems": problems,
        "assessments": assessments,
        "badges": earned_badges,
        "next_badges": progress.PROGRESS_BADGES + [progress.DEFAULT_PROFICIENCY_RULE],
        "activity_history": [_activity_out(h) for h in history],
        "xp": rewards.topic_total_xp(student_id, topic_oid_str),
    }


def _activity_out(doc):
    return {
        "id": str(doc["_id"]),
        "topic_id": doc.get("topic_id"),
        "type": doc.get("activity_type"),
        "ref": doc.get("activity_ref"),
        "description": doc.get("description"),
        "xp": doc.get("xp", 0),
        "at": doc.get("at"),
        "meta": doc.get("meta") or {},
    }
