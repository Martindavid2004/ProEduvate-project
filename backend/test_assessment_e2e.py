# test_assessment_e2e.py
"""
LIVE end-to-end test for BOTH MCQ assessment systems (teacher-assigned and
training/aptitude) against the real Flask app + MongoDB.

Exercises the task-spec state machine through ACTUAL HTTP routes:
  - start / status (server-authoritative expiry)
  - restart prevention (refresh, double start, repeated start)
  - TAB_SWITCH failure + locking
  - TIME_EXPIRED failure + locking
  - submit-after-failure rejected (terminal state never flips to PASS/FAIL)
  - normal submission -> PASS/FAIL with score
  - double submission -> only one terminal state
  - unique attempt index (race-proof start)

Run:  cd backend && ../.venv/Scripts/python.exe test_assessment_e2e.py
"""
import sys
import uuid

from bson import ObjectId

from app import create_app
from app.database import users_collection, submissions_collection, teacher_assignments_collection
from app.services import assessment_state

app = create_app()
client = app.test_client()

failures = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(f"{name}: {detail}")


suffix = uuid.uuid4().hex[:8]
uid = users_collection.insert_one({
    "name": f"MCQ-E2E {suffix}", "email": f"mcq_e2e_{suffix}@test.local", "role": "student",
}).inserted_id
UID = str(uid)

# A teacher assignment with 2 known MCQs (correct answers on the doc).
aid = str(teacher_assignments_collection.insert_one({
    "title": f"E2E Quiz {suffix}",
    "description": "temp",
    "type": "Quiz",
    "createdBy": "teacher",
    "quizQuestions": [
        {"question": "2+2?", "options": ["3", "4"], "correct_answer": "4"},
        {"question": "Capital of France?", "options": ["London", "Paris"], "correct_answer": "Paris"},
    ],
}).inserted_id)


def attempt_key():
    return f"{aid}_{UID}"


def cleanup():
    """Delete this student's attempts only (keep the assignment until the end
    so subsequent blocks can still start new attempts)."""
    submissions_collection.delete_many({
        "$or": [
            {assessment_state._base_key_field(assessment_state.TYPE_TEACHER_QUIZ): attempt_key()},
            {"student_id": UID, "type": assessment_state.TYPE_APTITUDE},
        ]})


def cleanup_all():
    cleanup()
    teacher_assignments_collection.delete_one({"_id": ObjectId(aid)})
    users_collection.delete_one({"_id": uid})


# ===========================================================================
# TEACHER-ASSIGNED MCQ
# ===========================================================================
print("--- TEACHER MCQ: normal submission (TEST 4) ---")
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start',
                json={"student_id": UID})
check("T4 start -> 200", r.status_code == 200, str(r.get_json())[:120])
att = r.get_json()['attempt']
# DYNAMIC POOLING: the start response serves THIS attempt's randomized
# paper - answers below must map to the served order (as the frontend does).
t4_served = r.get_json().get('questions') or []
check("T4 start serves per-attempt questions",
      len(t4_served) == 2, f"n={len(t4_served)}")
check("T4 attempt IN_PROGRESS with server expiry",
      att['status'] == 'IN_PROGRESS' and att['expiresAt'] and att['startedAt'],
      f"{att['status']} expires={att['expiresAt']}")
check("T4 remainingSeconds <= duration",
      0 < att['remainingSeconds'] <= assessment_state.QUIZ_DURATION_MINUTES * 60,
      str(att['remainingSeconds']))

# Refresh-safety: status endpoint returns the SAME attempt.
r = client.get(f'/api/teacher/assignments/{aid}/assessment/status',
               query_string={"student_id": UID})
check("T9 refresh: status returns same active attempt (no new attempt)",
      r.get_json()['attempt']['id'] == att['id'] and r.get_json()['active'],
      f"same_id={r.get_json()['attempt']['id'] == att['id']}")

# Repeated start (double click / two tabs) must NOT create a second attempt.
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start',
                json={"student_id": UID})
check("B7 repeated start returns same attempt (created=False)",
      r.get_json()['created'] is False and r.get_json()['attempt']['id'] == att['id'],
      f"created={r.get_json()['created']}")

t4_answers = {str(i): q["correct_answer"] for i, q in enumerate(t4_served)}
r = client.post(f'/api/teacher/assignments/{aid}/assessment/submit',
                json={"student_id": UID, "answers": t4_answers})
check("T4 submit -> 200", r.status_code == 200, str(r.get_json())[:150])
res = r.get_json()['result']
check("T4 all correct -> PASS with score 100",
      res['status'] == 'PASS' and res['passed'] is True and res['score'] == 100,
      f"status={res['status']} score={res['score']}")
check("T4 submitted_at stored", bool(res['submittedAt']), str(res['submittedAt']))

# Submit again -> rejected (TEST 11, double submission)
r = client.post(f'/api/teacher/assignments/{aid}/assessment/submit',
                json={"student_id": UID, "answers": t4_answers})
check("T11 double submit -> 409", r.status_code == 409, f"status={r.status_code}")

cleanup()

print("--- TEACHER MCQ: tab switch (TEST 6) + submit-after-fail (TEST 10) ---")
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start', json={"student_id": UID})
r = client.post(f'/api/teacher/assignments/{aid}/assessment/fail',
                json={"student_id": UID, "reason": "TAB_SWITCH"})
check("T6 fail TAB_SWITCH -> 200", r.status_code == 200, str(r.get_json())[:120])
att = r.get_json()['attempt']
check("T6 status=FAILED reason=TAB_SWITCH",
      att['status'] == 'FAILED' and att['failureReason'] == 'TAB_SWITCH',
      f"{att['status']}/{att['failureReason']}")
check("T6 failed attempt stores score 0", att['score'] == 0, str(att['score']))

# Refresh afterwards: still locked, same failed attempt.
r = client.get(f'/api/teacher/assignments/{aid}/assessment/status',
               query_string={"student_id": UID})
att2 = r.get_json()['attempt']
check("T6 refresh keeps FAILED/TAB_SWITCH (no restart)",
      att2['status'] == 'FAILED' and att2['failureReason'] == 'TAB_SWITCH'
      and att2['id'] == att['id'], f"{att2['status']}/{att2['failureReason']}")

# Start again -> must return the SAME failed attempt (no new attempt).
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start', json={"student_id": UID})
check("B7 start after FAIL returns locked attempt (created=False)",
      r.get_json()['created'] is False and r.get_json()['attempt']['status'] == 'FAILED',
      f"created={r.get_json()['created']} status={r.get_json()['attempt']['status']}")

# Submit after failure -> rejected, state remains FAILED (TEST 10).
# Answers are irrelevant here (submission is rejected), serve-shape payload.
r = client.post(f'/api/teacher/assignments/{aid}/assessment/submit',
                json={"student_id": UID, "answers": t4_answers})
check("T10 submit after TAB_SWITCH fail -> 409, still FAILED",
      r.status_code == 409 and r.get_json()['attempt']['status'] == 'FAILED',
      f"status={r.status_code} attempt={r.get_json().get('attempt', {}).get('status')}")
check("T10 terminal state never flips to PASS/FAIL",
      r.get_json()['attempt']['failureReason'] == 'TAB_SWITCH',
      str(r.get_json()['attempt'].get('failureReason')))

cleanup()

print("--- TEACHER MCQ: time expiry (TEST 5) ---")
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start', json={"student_id": UID})
att = r.get_json()['attempt']
# Simulate expiry by backdating the server-side expiry in the DB.
submissions_collection.update_one(
    {"_id": ObjectId(att['id'])},
    {"$set": {"assessment_expires_at": __import__('datetime').datetime.utcnow()}})
# Any status/fail/submit call must now finalize as FAILED/TIME_EXPIRED.
r = client.get(f'/api/teacher/assignments/{aid}/assessment/status',
               query_string={"student_id": UID})
att = r.get_json()['attempt']
check("T5 expired attempt auto-finalizes FAILED/TIME_EXPIRED on status",
      att['status'] == 'FAILED' and att['failureReason'] == 'TIME_EXPIRED',
      f"{att['status']}/{att['failureReason']}")

# Late submission must be rejected (B3: server-side enforcement).
client.post(f'/api/teacher/assignments/{aid}/assessment/fail',
            json={"student_id": UID, "reason": "TIME_EXPIRED"})
cleanup()

print("--- TEACHER MCQ: late submit lands as FAILED/TIME_EXPIRED (B9) ---")
r = client.post(f'/api/teacher/assignments/{aid}/assessment/start', json={"student_id": UID})
att = r.get_json()['attempt']
submissions_collection.update_one(
    {"_id": ObjectId(att['id'])},
    {"$set": {"assessment_expires_at": __import__('datetime').datetime.utcnow()}})
r = client.post(f'/api/teacher/assignments/{aid}/assessment/submit',
                json={"student_id": UID, "answers": t4_answers})
check("B9 late submit -> 409 with FAILED/TIME_EXPIRED",
      r.status_code == 409
      and r.get_json().get('attempt', {}).get('failureReason') == 'TIME_EXPIRED',
      f"status={r.status_code} reason={r.get_json().get('failureReason')}")
check("B9 score not accepted as normal result",
      r.get_json().get('attempt', {}).get('score') == 0,
      str(r.get_json().get('attempt', {}).get('score')))
cleanup()

# ===========================================================================
# TRAINING MCQ (aptitude)
# ===========================================================================
print("--- TRAINING MCQ: tab switch (TEST 8) ---")
TOPIC = "Percentage"
r = client.post('/api/aptitude/test/generate', json={
    "topic": TOPIC, "difficulty": "medium", "num_questions": 2, "student_id": UID})
check("T8 generate test -> 200", r.status_code == 200, str(r.get_json())[:120])
data = r.get_json()
tid = data['test_id']
att = data.get('attempt') or {}
check("T8 attempt created with server expiry",
      att.get('status') == 'IN_PROGRESS' and att.get('expiresAt'),
      f"{att.get('status')} expires={att.get('expiresAt')}")
check("T8 questions stored on attempt (refresh-safe)", len(data.get('questions') or []) > 0,
      f"n={len(data.get('questions') or [])}")

r = client.post('/api/aptitude/test/fail', json={
    "test_id": tid, "reason": "TAB_SWITCH", "student_id": UID, "topic": TOPIC})
check("T8 fail TAB_SWITCH -> 200", r.status_code == 200, str(r.get_json())[:120])
att = r.get_json()['attempt']
check("T8 FAILED/TAB_SWITCH stored",
      att['status'] == 'FAILED' and att['failureReason'] == 'TAB_SWITCH',
      f"{att['status']}/{att['failureReason']}")

# Regenerate (frontend start button) -> 409 lock, no restart.
r = client.post('/api/aptitude/test/generate', json={
    "topic": TOPIC, "difficulty": "medium", "num_questions": 2, "student_id": UID})
check("T8 regenerate after fail -> 409 locked",
      r.status_code == 409 and r.get_json().get('failureReason') == 'TAB_SWITCH',
      f"status={r.status_code} reason={r.get_json().get('failureReason')}")

# Submit after fail -> 409, still FAILED (TEST 10).
r = client.post('/api/aptitude/test/submit', json={
    "student_id": UID, "test_id": tid, "topic": TOPIC,
    "questions": [{"question": "q", "options": ["a"], "correct_answer": "a"}],
    "answers": {"0": "a"}, "time_taken": 10})
check("T10 training submit after fail -> 409",
      r.status_code == 409, f"status={r.status_code}")

cleanup()

print("--- TRAINING MCQ: time expiry (TEST 7) ---")
r = client.post('/api/aptitude/test/generate', json={
    "topic": TOPIC, "difficulty": "medium", "num_questions": 2, "student_id": UID})
tid = r.get_json()['test_id']
submissions_collection.update_one(
    {"_id": ObjectId(tid)},
    {"$set": {"assessment_expires_at": __import__('datetime').datetime.utcnow()}})
r = client.post('/api/aptitude/test/fail', json={
    "test_id": tid, "reason": "TIME_EXPIRED", "student_id": UID, "topic": TOPIC})
att = r.get_json()['attempt']
check("T7 FAILED/TIME_EXPIRED stored",
      att['status'] == 'FAILED' and att['failureReason'] == 'TIME_EXPIRED',
      f"{att['status']}/{att['failureReason']}")
r = client.post('/api/aptitude/test/generate', json={
    "topic": TOPIC, "difficulty": "medium", "num_questions": 2, "student_id": UID})
check("T7 regenerate after expiry -> 409 locked",
      r.status_code == 409 and r.get_json().get('failureReason') == 'TIME_EXPIRED',
      f"status={r.status_code} reason={r.get_json().get('failureReason')}")
cleanup()

print("--- TRAINING MCQ: normal submission + double submit (TEST 11) ---")
r = client.post('/api/aptitude/test/generate', json={
    "topic": TOPIC, "difficulty": "medium", "num_questions": 2, "student_id": UID})
data = r.get_json()
tid = data['test_id']
qs = data['questions']
answers = {str(i): q['correct_answer'] for i, q in enumerate(qs)}
r = client.post('/api/aptitude/test/submit', json={
    "student_id": UID, "test_id": tid, "topic": TOPIC,
    "questions": qs, "answers": answers, "time_taken": 120})
check("T4b training submit -> 200 PASS",
      r.status_code == 200 and r.get_json().get('evaluation', {}).get('passed') is True,
      f"status={r.status_code} passed={r.get_json().get('evaluation', {}).get('passed')} score={r.get_json().get('evaluation', {}).get('score')}")
r = client.post('/api/aptitude/test/submit', json={
    "student_id": UID, "test_id": tid, "topic": TOPIC,
    "questions": qs, "answers": answers, "time_taken": 120})
check("T11 training double submit -> 409", r.status_code == 409, f"status={r.status_code}")

cleanup()

print("--- Unique attempt index exists (B7 race-proofing) ---")
from app.database import db
idx_info = submissions_collection.index_information()
uniq_quiz = idx_info.get('uniq_quiz_assessment_key')
uniq_apt = idx_info.get('uniq_aptitude_key')
check("unique index on quiz_assessment_key", bool(uniq_quiz and uniq_quiz.get('unique')),
      str(uniq_quiz))
check("unique index on aptitude_key", bool(uniq_apt and uniq_apt.get('unique')),
      str(uniq_apt))

print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(" -", f)
    cleanup_all()
    sys.exit(1)
cleanup_all()
print("ALL MCQ ASSESSMENT E2E TESTS PASSED")
