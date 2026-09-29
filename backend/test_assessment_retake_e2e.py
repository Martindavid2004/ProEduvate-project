# test_assessment_retake_e2e.py
"""
Live E2E verification of the assessment overhaul (backend, real Atlas DB).

Covers:
  1. Retake flow (aptitude): after a finished attempt, /test/generate with
     retake=True archives the old attempt and starts a fresh one; without
     retake it returns 409 with canRetake=True (no permanent lockout).
  2. /test/status endpoint reports attempt state + lastResult + canRetake.
  3. Quiz retake: /assessment/start with retake=True archives a finished
     quiz attempt and creates a new IN_PROGRESS attempt.
  4. Score sync: a finished aptitude attempt surfaces on
     /api/student/<id>/progress (aptitudeScore/quizScore) and a finished
     quiz attempt surfaces on /api/student/<id>/assignments with score +
     status + evaluation for the answer-review view.
  5. Dynamic question pool: expanded/shuffled pool returns >= curated size
     and is valid.

Run:  cd backend && ./venv/Scripts/python.exe test_assessment_retake_e2e.py
(requires the backend venv - uses app context + Atlas from backend/.env)
"""
import sys
import uuid
from datetime import datetime

sys.path.insert(0, ".")

from app import create_app
from app.database import (
    users_collection,
    submissions_collection,
    teacher_assignments_collection,
)
from app.services import assessment_state

failures = []
app = None  # set in main()


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(name)


def _unique_email():
    return f"retake_e2e_{uuid.uuid4().hex[:10]}@test.com"


def main():
    global app
    app = create_app()
    with app.app_context():
        suffix = uuid.uuid4().hex[:8]

        # ---------------- Seed student ----------------
        user = {
            "name": f"Retake E2E {suffix}",
            "email": _unique_email(),
            "password": "x",
            "role": "student",
        }
        uid = str(users_collection.insert_one(user).inserted_id)

        try:
            # ============ 1. APTITUDE RETAKE FLOW ============
            topic = "Number System"
            key = f"{topic}_{uid}"

            # Start attempt 1
            st1, r1 = _gen(uid, topic, retake=False)
            check("aptitude start: fresh attempt created",
                  st1 == 200 and r1.get("success") and r1.get("created") is True,
                  f"st={st1} created={r1.get('created')}")
            n1 = len(r1.get("questions") or [])
            check("aptitude start: questions present", n1 > 0, f"n={n1}")

            # Finish attempt 1 (fail via tab switch)
            stf, rf = _fail(uid, topic)
            check("aptitude fail: attempt FAILED/TAB_SWITCH",
                  stf == 200 and rf.get("attempt", {}).get("status") == "FAILED",
                  f"st={stf} status={rf.get('attempt', {}).get('status')}")

            # Without retake -> 409 + canRetake=True (no permanent lockout)
            st2, r2 = _gen(uid, topic, retake=False)
            check("aptitude restart w/o retake -> 409 canRetake",
                  st2 == 409 and r2.get("canRetake") is True,
                  f"st={st2} canRetake={r2.get('canRetake')}")

            # Status endpoint: lastResult present, canRetake=True
            sts, rs = _status(uid, topic)
            check("aptitude status: lastResult + canRetake",
                  sts == 200 and rs.get("canRetake") is True
                  and rs.get("lastResult", {}).get("status") == "FAILED",
                  f"st={sts} last={rs.get('lastResult', {}).get('status')} canRetake={rs.get('canRetake')}")

            # WITH retake -> new attempt, old one archived
            st3, r3 = _gen(uid, topic, retake=True)
            check("aptitude retake: fresh attempt created",
                  st3 == 200 and r3.get("success") and r3.get("created") is True,
                  f"st={st3} created={r3.get('created')}")
            check("aptitude retake: new attempt IN_PROGRESS",
                  r3.get("attempt", {}).get("status") == "IN_PROGRESS",
                  f"status={r3.get('attempt', {}).get('status')}")

            old = submissions_collection.find_one({
                "retired_attempt_key": key, "retired": True})
            check("aptitude retake: old attempt archived (kept, not deleted)",
                  old is not None and old.get("status") == "FAILED",
                  f"old status={old and old.get('status')}")

            # Exactly one live attempt for the key
            live = list(submissions_collection.find({
                "aptitude_key": key, "status": {"$ne": None}}))
            live_active = [d for d in live if d.get("retired") is not True]
            check("aptitude retake: exactly one live attempt",
                  len(live_active) == 1, f"live={len(live_active)}")

            # ============ 2. SCORE SYNC ============
            # Submit attempt 2 with ALL answers correct -> deterministic 100%
            # regardless of how many questions the AI expansion produced
            # (the old qs[:10] slice made the score depend on pool size).
            qs = r3.get("questions") or []
            answers = {}
            for i, q in enumerate(qs):
                answers[str(i)] = q.get("correct_answer")
            stsub, rsub = _submit(uid, topic, qs, answers)
            check("aptitude submit: evaluated",
                  stsub == 200 and rsub.get("success"),
                  f"st={stsub} err={rsub.get('message')}")

            # Progress endpoint reflects the score (real-time, no N/A)
            stp, rp = _progress(uid)
            stats = rp.get("statistics", {}) if isinstance(rp, dict) and "statistics" in rp else None
            # The /api/aptitude/progress endpoint
            check("aptitude progress: total_tests >= 1",
                  stp == 200 and rp.get("statistics", {}).get("total_tests", 0) >= 1,
                  f"total={rp.get('statistics', {}).get('total_tests')}")

            # Student dashboard progress (/api/student/<id>/progress)
            stp2, rp2 = _student_progress(uid)
            check("dashboard: aptitudeScore present (score sync)",
                  stp2 == 200 and rp2.get("aptitudeScore") is not None,
                  f"aptitudeScore={rp2.get('aptitudeScore')} total={rp2.get('totalAptitudeTests')}")
            # Two finished attempts: the tab-switch FAIL (score 0 by
            # contract) + the 100% submit -> avg 50, best 100.
            check("dashboard: aptitudeScore == 50 (avg of 0 and 100)",
                  rp2.get("aptitudeScore") is not None and abs(rp2["aptitudeScore"] - 50.0) < 0.01,
                  f"aptitudeScore={rp2.get('aptitudeScore')}")
            check("dashboard: totalAptitudeTests == 2",
                  rp2.get("totalAptitudeTests") == 2,
                  f"total={rp2.get('totalAptitudeTests')}")
            check("dashboard: aptitudeBestScore == 100",
                  rp2.get("aptitudeBestScore") == 100,
                  f"best={rp2.get('aptitudeBestScore')}")
            # resumeUploaded must be False (no resume uploaded for this user)
            check("dashboard: resumeUploaded false (no fabricated default)",
                  rp2.get("resumeUploaded") is False,
                  f"resumeUploaded={rp2.get('resumeUploaded')}")

            # ============ 3. QUIZ RETAKE FLOW ============
            aid = _seed_quiz(suffix)
            qkey = f"{aid}_{uid}"

            stq1, rq1 = _quiz_start(aid, uid, retake=False)
            check("quiz start: fresh attempt",
                  stq1 == 200 and rq1.get("created") is True,
                  f"st={stq1} created={rq1.get('created')}")

            # Fail it via tab switch
            stqf, rqf = _quiz_fail(aid, uid)
            check("quiz fail: FAILED/TAB_SWITCH",
                  stqf == 200 and rqf.get("attempt", {}).get("status") == "FAILED",
                  f"st={stqf} status={rqf.get('attempt', {}).get('status')}")

            # Without retake -> locked attempt returned (not created)
            stq2, rq2 = _quiz_start(aid, uid, retake=False)
            check("quiz restart w/o retake: locked (created=False)",
                  stq2 == 200 and rq2.get("created") is False
                  and rq2.get("attempt", {}).get("status") == "FAILED",
                  f"st={stq2} status={rq2.get('attempt', {}).get('status')}")

            # With retake -> new IN_PROGRESS attempt, old archived
            stq3, rq3 = _quiz_start(aid, retake=True, uid=uid)
            check("quiz retake: fresh IN_PROGRESS attempt",
                  stq3 == 200 and rq3.get("attempt", {}).get("status") == "IN_PROGRESS",
                  f"st={stq3} status={rq3.get('attempt', {}).get('status')}")

            old_q = submissions_collection.find_one({
                "retired_attempt_key": qkey, "retired": True})
            check("quiz retake: old attempt archived",
                  old_q is not None and old_q.get("status") == "FAILED",
                  f"old status={old_q and old_q.get('status')}")

            # Submit the retake attempt (pass)
            # DYNAMIC POOLING: answers must map to the SERVED paper (the
            # attempt's randomized snapshot), exactly like the frontend does
            # - not the assignment's stored bank order.
            questions = rq3.get("questions") or _quiz_questions(aid)
            answers = {str(i): q["correct_answer"] for i, q in enumerate(questions)}
            stqs, rqs = _quiz_submit(aid, uid, answers)
            check("quiz retake submit: evaluated PASS",
                  stqs == 200 and rqs.get("result", {}).get("status") == "PASS",
                  f"st={stqs} status={rqs.get('result', {}).get('status')}")

            # Assignments endpoint: quiz now surfaces as submitted with score
            sta, ra = _student_assignments(uid)
            match = next((a for a in (ra if isinstance(ra, list) else [])
                          if a.get("id") == aid), None)
            check("assignments: quiz surfaces as submitted",
                  sta == 200 and match is not None and match.get("submitted") is True,
                  f"st={sta} match={bool(match)} submitted={match and match.get('submitted')}")
            check("assignments: quiz_score + quiz_status present",
                  match is not None and match.get("quiz_score") is not None
                  and match.get("quiz_status") == "PASS",
                  f"score={match and match.get('quiz_score')} status={match and match.get('quiz_status')}")
            check("assignments: quiz_evaluation present (answer review)",
                  match is not None and match.get("quiz_evaluation", {}).get("results"),
                  f"results={len((match or {}).get('quiz_evaluation', {}).get('results') or [])}")

            # Retaking the quiz again after completion works (retake -> PASS state archived)
            stq4, rq4 = _quiz_start(aid, retake=True, uid=uid)
            check("quiz retake after completion: fresh attempt",
                  stq4 == 200 and rq4.get("attempt", {}).get("status") == "IN_PROGRESS",
                  f"st={stq4} status={rq4.get('attempt', {}).get('status')}")

            # ============ 5. DYNAMIC QUESTION POOL ============
            stg, rg = _gen(uid, "Averages", retake=True)
            check("pool: generated questions valid",
                  stg == 200 and len(rg.get("questions") or []) > 0,
                  f"n={len(rg.get('questions') or [])}")
            pool = rg.get("questions") or []
            texts = [q.get("question", "").strip().lower() for q in pool]
            check("pool: no duplicate questions",
                  len(texts) == len(set(texts)),
                  f"n={len(texts)} unique={len(set(texts))}")
            trivial = [t for t in texts if t in ("what is 2+2?", "what is 2 + 2?")]
            check("pool: no trivial '2+2' questions",
                  len(trivial) == 0, f"trivial={trivial}")

        finally:
            # Cleanup throwaway E2E data
            submissions_collection.delete_many({"$or": [
                {"student_id": uid},
                {"retired_attempt_key": {"$regex": uid}},
                {"quiz_assessment_key": {"$regex": uid}},
                {"aptitude_key": {"$regex": uid}},
            ]})
            teacher_assignments_collection.delete_many(
                {"title": {"$regex": f"RetakeE2E {suffix}"}})
            users_collection.delete_one({"_id": _oid(uid)})
            print("\n[CLEANUP] throwaway E2E data removed")

        print("\n===== RETAKE E2E SUMMARY =====")
        if failures:
            print(f"FAILURES ({len(failures)}):")
            for f in failures:
                print(f"  - {f}")
            sys.exit(1)
        print("ALL RETAKE/SCORE-SYNC E2E CHECKS PASSED")


def _oid(uid):
    from bson import ObjectId
    return ObjectId(uid)


def _gen(uid, topic, retake=False):
    from app.routes.aptitude_routes import generate_test
    from flask import Flask  # noqa: F401
    # Call the Flask view functions directly inside a test request context
    with app.test_request_context(
            "/api/aptitude/test/generate", method="POST",
            json={"student_id": uid, "topic": topic, "retake": retake,
                  "num_questions": 50}):
        from flask import jsonify  # noqa: F401
        resp, code = generate_test()
        return code, resp.get_json()


def _fail(uid, topic):
    from app.routes.aptitude_routes import fail_test
    attempt = submissions_collection.find_one({"aptitude_key": f"{topic}_{uid}"})
    with app.test_request_context(
            "/api/aptitude/test/fail", method="POST",
            json={"test_id": str(attempt["_id"]), "reason": "TAB_SWITCH",
                  "student_id": uid, "topic": topic}):
        resp, code = fail_test()
        return code, resp.get_json()


def _submit(uid, topic, questions, answers):
    from app.routes.aptitude_routes import submit_test
    attempt = submissions_collection.find_one({"aptitude_key": f"{topic}_{uid}"})
    with app.test_request_context(
            "/api/aptitude/test/submit", method="POST",
            json={"test_id": str(attempt["_id"]), "topic": topic,
                  "questions": questions, "answers": answers,
                  "student_id": uid, "time_taken": 60}):
        resp, code = submit_test()
        return code, resp.get_json()


def _status(uid, topic):
    from app.routes.aptitude_routes import get_test_status
    with app.test_request_context(
            f"/api/aptitude/test/status?topic={topic}&student_id={uid}",
            method="GET"):
        resp, code = get_test_status()
        return code, resp.get_json()


def _progress(uid):
    from app.routes.aptitude_routes import get_progress
    with app.test_request_context(f"/api/aptitude/progress/{uid}", method="GET"):
        resp, code = get_progress(uid)
        return code, resp.get_json()


def _student_progress(uid):
    from app.routes.student_routes import get_student_progress
    with app.test_request_context(f"/api/student/{uid}/progress", method="GET"):
        resp, code = get_student_progress(uid)
        return code, resp.get_json()


def _student_assignments(uid):
    from app.routes.student_routes import get_student_assignments_by_id
    with app.test_request_context(f"/api/student/{uid}/assignments", method="GET"):
        resp, code = get_student_assignments_by_id(uid)
        return code, resp.get_json()


def _seed_quiz(suffix):
    a = {
        "title": f"RetakeE2E {suffix} Quiz",
        "description": "retake e2e",
        "dueDate": "2026-12-31",
        "type": "Quiz",
        "createdBy": "teacher",
        "quizQuestions": [
            {"question": "2+3=?", "options": ["4", "5", "6", "7"], "correct_answer": "5"},
            {"question": "Capital of France?", "options": ["London", "Paris", "Rome", "Berlin"], "correct_answer": "Paris"},
            {"question": "15% of 200?", "options": ["25", "30", "35", "40"], "correct_answer": "30"},
        ],
    }
    return str(teacher_assignments_collection.insert_one(a).inserted_id)


def _quiz_questions(aid):
    doc = teacher_assignments_collection.find_one(_oid(aid))
    return doc.get("quizQuestions") or []


def _quiz_start(aid, uid=None, retake=False, **_):
    from app.routes.teacher_routes import start_quiz_assessment
    with app.test_request_context(
            f"/api/teacher/assignments/{aid}/assessment/start", method="POST",
            json={"student_id": uid, "retake": retake}):
        resp, code = start_quiz_assessment(aid)
        return code, resp.get_json()


def _quiz_fail(aid, uid):
    from app.routes.teacher_routes import fail_quiz_assessment
    with app.test_request_context(
            f"/api/teacher/assignments/{aid}/assessment/fail", method="POST",
            json={"student_id": uid, "reason": "TAB_SWITCH"}):
        resp, code = fail_quiz_assessment(aid)
        return code, resp.get_json()


def _quiz_submit(aid, uid, answers):
    from app.routes.teacher_routes import submit_quiz_assessment
    with app.test_request_context(
            f"/api/teacher/assignments/{aid}/assessment/submit", method="POST",
            json={"student_id": uid, "answers": answers}):
        resp, code = submit_quiz_assessment(aid)
        return code, resp.get_json()


if __name__ == "__main__":
    main()
