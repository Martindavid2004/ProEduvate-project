# test_interview_e2e.py
"""
LIVE end-to-end test for the Mock Interview API against the real Flask app
and the real MongoDB (Atlas).

Flow exercised (actual HTTP, actual DB):
  1. POST /api/interview/start            -> session created
  2. POST /api/interview/answer  x3       -> answers persisted (200, no 404)
  3. POST /api/interview/answer (bad id)  -> 404 + ownership check
  4. POST /api/interview/evaluate         -> evidence-based result stored
  5. Re-evaluate                          -> idempotent (same stored result)
  6. POST /api/interview/answer after completion -> 409 locked

Run:  cd backend && ../.venv/Scripts/python.exe test_interview_e2e.py
"""
import sys
import uuid

from app import create_app
from app.database import users_collection, submissions_collection

app = create_app()
client = app.test_client()

failures = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(f"{name}: {detail}")


# Create a throwaway student so the ownership checks are exercised honestly.
suffix = uuid.uuid4().hex[:8]
user_doc = {
    "name": f"IT-E2E {suffix}",
    "email": f"it_e2e_{suffix}@test.local",
    "role": "student",
}
uid = users_collection.insert_one(user_doc).inserted_id
UID = str(uid)

Q_REACT = "What is your experience with React?"
questions = [Q_REACT, "How do you approach debugging?", "Describe a team conflict you resolved.",
             "Tell me about SQL.", "Question five?"]

# ---------------------------------------------------------------------------
# 0. RESUME UPLOAD GATEWAY: starting without a resume must be rejected.
# ---------------------------------------------------------------------------
r = client.post('/api/interview/start', json={"user_id": UID, "mode": "text"})
check("start WITHOUT resume -> 400 RESUME_REQUIRED", r.status_code == 400
      and r.get_json().get('code') == 'RESUME_REQUIRED',
      f"status={r.status_code} body={str(r.get_json())[:120]}")

# Give the throwaway student a resume (as upload_resume would) so the
# interview can start.
users_collection.update_one({"_id": uid}, {"$set": {
    "resume_text": "Jane Doe - B.Tech CSE. Skills: React, SQL, Docker. "
                   "Projects: ResumeE2E Dashboard - React, MongoDB.",
    "resume_filename": f"e2e_{UID}.pdf",
}})

# ---------------------------------------------------------------------------
# 1. Start interview (resume on file now)
# ---------------------------------------------------------------------------
r = client.post('/api/interview/start', json={"user_id": UID, "mode": "text"})
check("start interview with resume -> 200", r.status_code == 200, f"status={r.status_code} body={str(r.get_json())[:150]}")
data = r.get_json()
sid = data['session']['sessionId']
# Overwrite with a fixed 5-question deck so relevance cases are deterministic.
submissions_collection.update_one({"_id": __import__('bson').ObjectId(sid)},
                                  {"$set": {"questions": questions}})

# ---------------------------------------------------------------------------
# 2. Save answers (THE previous 404 case)
# ---------------------------------------------------------------------------
r = client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": UID, "question_index": 0,
    "answer": "I worked on a React project where I built reusable components and used hooks.",
    "transcript_status": "VALID",
})
check("answer 1 -> 200 (no 404)", r.status_code == 200, f"status={r.status_code} body={str(r.get_json())[:150]}")
check("answer 1 response carries session", r.get_json().get('session', {}).get('sessionId') == sid)

r = client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": UID, "question_index": 1,
    "answer": "I went to the beach yesterday and watched a movie.",
})
check("answer 2 (irrelevant) -> 200", r.status_code == 200, f"status={r.status_code}")

r = client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": UID, "question_index": 2,
    "answer": "I led the team standups and mentored two interns on our React codebase.",
})
check("answer 3 -> 200", r.status_code == 200, f"status={r.status_code}")

# Verify DB persistence: structured turns exist, question text captured.
doc = submissions_collection.find_one({"_id": __import__('bson').ObjectId(sid)})
turns = doc.get('answer_turns') or []
check("3 structured turns stored in DB", len(turns) == 3, f"turns={len(turns)}")
check("turns carry question text", all(t.get('question') for t in turns),
      str([t.get('question', '')[:30] for t in turns]))
check("turns carry STT status", turns[0].get('transcript_status') == 'VALID',
      str(turns[0].get('transcript_status')))
check("turn carries timestamp", isinstance(turns[0].get('saved_at'), object))

# Duplicate save for same question index = update, not duplicate.
client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": UID, "question_index": 0,
    "answer": "I worked on a React project where I built reusable components and used hooks, and unit tested them.",
    "transcript_status": "VALID",
})
doc = submissions_collection.find_one({"_id": __import__('bson').ObjectId(sid)})
check("re-saving same question updates, not duplicates",
      len(doc.get('answer_turns') or []) == 3, f"turns={len(doc.get('answer_turns') or [])}")

# ---------------------------------------------------------------------------
# 3. Wrong owner / foreign session -> 404
# ---------------------------------------------------------------------------
r = client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": "000000000000000000000000", "question_index": 3,
    "answer": "hijack attempt",
})
check("answer with wrong user -> 404", r.status_code == 404, f"status={r.status_code}")
r = client.post('/api/interview/answer', json={
    "session_id": "111111111111111111111111", "user_id": UID, "question_index": 3,
    "answer": "stale id",
})
check("answer with stale session id -> 404", r.status_code == 404, f"status={r.status_code}")

# ---------------------------------------------------------------------------
# 4. Evaluate -> evidence-based result stored
# ---------------------------------------------------------------------------
r = client.post('/api/interview/evaluate', json={
    "session_id": sid, "user_id": UID,
    "questions": questions,
    "answers": ["I worked on a React project where I built reusable components and used hooks, and unit tested them.",
                "I went to the beach yesterday and watched a movie.",
                "I led the team standups and mentored two interns on our React codebase.",
                "", ""],
})
check("evaluate -> 200", r.status_code == 200, f"status={r.status_code} body={str(r.get_json())[:200]}")
res = r.get_json()
check("result has evidence-based method flag", res.get('evaluation_method') == 'evidence_based',
      str(res.get('evaluation_method')))
check("relevant answer classified RELEVANT", res['details'][0]['classification'] == 'RELEVANT',
      res['details'][0]['classification'])
check("irrelevant answer classified IRRELEVANT", res['details'][1]['classification'] == 'IRRELEVANT',
      res['details'][1]['classification'])
check("missing answers classified NO_ANSWER",
      res['details'][3]['classification'] == 'NO_ANSWER' and res['details'][4]['classification'] == 'NO_ANSWER',
      f"{res['details'][3]['classification']}/{res['details'][4]['classification']}")
check("final score is honest (mixed interview)", 5 <= res['score'] <= 40, f"score={res['score']}")
check("mixed interview FAILED at 60% pass mark",
      res.get('passed') is False and res.get('status') == 'FAIL' and res.get('pass_mark') == 60.0,
      f"passed={res.get('passed')} status={res.get('status')} pass_mark={res.get('pass_mark')}")
check("session stored result", doc is not None)

doc = submissions_collection.find_one({"_id": __import__('bson').ObjectId(sid)})
check("DB session status=completed", doc.get('status') == 'completed', doc.get('status'))
check("DB score == response score", abs((doc.get('score') or -1) - res['score']) < 0.01,
      f"db={doc.get('score')} resp={res['score']}")
check("DB result.evaluation_method=evidence_based",
      (doc.get('result') or {}).get('evaluation_method') == 'evidence_based')
check("DB session interview_status=FAIL",
      doc.get('interview_status') == 'FAIL', doc.get('interview_status'))

user_after = users_collection.find_one({"_id": uid})
check("user.interviewScore updated to real score",
      abs((user_after.get('interviewScore') or -1) - res['score']) < 0.01,
      f"user={user_after.get('interviewScore')} expected={res['score']}")
check("user.interviewStatus persisted (FAIL)",
      user_after.get('interviewStatus') == 'FAIL', user_after.get('interviewStatus'))

# ---------------------------------------------------------------------------
# 5. Idempotent re-evaluation
# ---------------------------------------------------------------------------
r2 = client.post('/api/interview/evaluate', json={
    "session_id": sid, "user_id": UID, "questions": questions, "answers": ["x"] * 5,
})
check("re-evaluate -> 200 with STORED result (not re-scored)",
      r2.status_code == 200 and r2.get_json().get('score') == res['score'],
      f"score={r2.get_json().get('score')} stored={res['score']}")

# ---------------------------------------------------------------------------
# 6. Answer after completion -> 409
# ---------------------------------------------------------------------------
r = client.post('/api/interview/answer', json={
    "session_id": sid, "user_id": UID, "question_index": 3, "answer": "late answer",
})
check("answer after completion -> 409", r.status_code == 409, f"status={r.status_code}")

# ---------------------------------------------------------------------------
# Empty-transcript rejection path (frontend would never send this, but the
# API must not treat an empty answer as a valid turn either)
# ---------------------------------------------------------------------------
r = client.post('/api/interview/start', json={"user_id": UID, "mode": "text"})
sid2 = r.get_json()['session']['sessionId']
submissions_collection.update_one({"_id": __import__('bson').ObjectId(sid2)},
                                  {"$set": {"questions": questions}})
r = client.post('/api/interview/evaluate', json={
    "session_id": sid2, "user_id": UID, "questions": questions, "answers": ["", "", "", "", ""],
})
res2 = r.get_json()
check("all-empty evaluate -> score 0", r.status_code == 200 and res2['score'] == 0,
      f"status={r.status_code} score={res2.get('score')}")
check("all-empty feedback says no valid answers",
      'No valid substantive answers' in res2.get('feedback', ''), res2.get('feedback', '')[:80])
check("all-empty -> FAIL status", res2.get('status') == 'FAIL', res2.get('status'))

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
users_collection.delete_one({"_id": uid})
submissions_collection.delete_many({"_id": {"$in": [__import__('bson').ObjectId(sid),
                                                    __import__('bson').ObjectId(sid2)]}})

print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("ALL E2E INTERVIEW TESTS PASSED")
