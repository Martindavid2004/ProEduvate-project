"""Live E2E: resume gate + OLLAMA resume-based interview questions.

Flow (real Flask app, real MongoDB, real local Ollama at OLLAMA_BASE_URL):
  1. create throwaway student (no resume)
  2. POST /api/interview/start            -> 400 RESUME_REQUIRED (gate)
  3. generate a realistic PDF resume (MedVision AI - FastAPI, React, MongoDB)
  4. POST /api/student/<uid>/upload_resume -> parsed + persisted
  5. POST /api/interview/start            -> 10 questions via OLLAMA with
     [EASY]/[MEDIUM]/[HARD] tags and the 40/40/20 distribution
  6. answer one turn + evaluate            -> full interview lifecycle works
  7. cleanup (user, session, uploaded file)

Run:  cd backend && python test_interview_resume_e2e_ollama.py
"""
import io
import os
import re
import sys
import uuid

import fitz  # PyMuPDF

from app import create_app
from app.database import users_collection, submissions_collection
from app.services.ai_service import OLLAMA_BASE_URL, OLLAMA_MODEL

app = create_app()
client = app.test_client()

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(f"{name}: {detail}")


RESUME_LINES = [
    "JANE DOE",
    "B.Tech Computer Science, 2026",
    "PROJECTS",
    "MedVision AI - FastAPI, React, MongoDB",
    "Built a medical imaging triage platform with a FastAPI backend,",
    "a React dashboard and MongoDB for storing DICOM study metadata.",
    "SKILLS",
    "Python, FastAPI, React, MongoDB, Docker, Git",
]

print(f"Ollama target: {OLLAMA_BASE_URL} (model={OLLAMA_MODEL})")

# --- 1. throwaway user WITHOUT a resume ---
suffix = uuid.uuid4().hex[:8]
uid = users_collection.insert_one({
    "name": f"OllamaE2E {suffix}",
    "email": f"ollama_e2e_{suffix}@test.local",
    "role": "student",
}).inserted_id
UID = str(uid)

# --- 2. RESUME GATE: starting without a resume must be rejected ---
r = client.post("/api/interview/start", json={"user_id": UID, "mode": "text"})
body = r.get_json() or {}
check("start interview WITHOUT resume -> 400", r.status_code == 400,
      f"status={r.status_code} body={str(body)[:120]}")
check("gate error code is RESUME_REQUIRED", body.get("code") == "RESUME_REQUIRED",
      str(body.get("code")))
check("no interview session was created",
      not r.get_json().get("session"), "session must be absent on a gated start")

# --- 3. build the resume PDF ---
pdf = fitz.open()
page = pdf.new_page()
y = 60
for line in RESUME_LINES:
    page.insert_text((50, y), line, fontsize=11)
    y += 20
buf = pdf.tobytes()
pdf.close()

# --- 4. upload + parse resume ---
r = client.post(f"/api/student/{UID}/upload_resume", data={
    "resume": (io.BytesIO(buf), "jane_doe_resume.pdf"),
}, content_type="multipart/form-data")
check("upload resume -> 200", r.status_code == 200,
      f"status={r.status_code} body={str(r.get_json())[:120]}")

user = users_collection.find_one({"_id": uid})
check("resume_text persisted on user",
      "MedVision AI" in (user.get("resume_text") or ""),
      f"chars={len(user.get('resume_text') or '')}")

# --- 5. start interview: Ollama must generate the resume-grounded deck ---
print("\n--- backend logs (interview start) ---")
r = client.post("/api/interview/start", json={"user_id": UID, "mode": "text"})
check("start interview -> 200", r.status_code == 200, f"status={r.status_code}")
data = r.get_json()
questions = data.get("questions") or []
sid = (data.get("session") or {}).get("sessionId")
print(f"--- {len(questions)} questions generated ---")
for i, q in enumerate(questions, 1):
    print(f"  Q{i}: {q[:150]}")

joined = " ".join(questions)
tagged = [q for q in questions if re.match(r"^\[(EASY|MEDIUM|HARD)\]", q)]
dist = {"easy": 0, "medium": 0, "hard": 0}
for q in questions:
    m = re.match(r"^\[(EASY|MEDIUM|HARD)\]", q)
    if m:
        dist[m.group(1).lower()] += 1

check("10 questions generated", len(questions) == 10, f"n={len(questions)}")
check("questions came from the OLLAMA path ([DIFFICULTY] tags present)",
      len(tagged) == 10,
      f"tagged={len(tagged)}/10 (untagged => fell back to Gemini/offline)")
check("difficulty mix is 40/40/20 (4 easy / 4 medium / 2 hard)",
      dist == {"easy": 4, "medium": 4, "hard": 2}, str(dist))
check("every question carries a valid difficulty tag",
      all(m for q in questions for m in [re.match(r"^\[(EASY|MEDIUM|HARD)\]", q)]),
      "")
check("questions reference the resume project/skills",
      any(k in joined.lower() for k in ("medvision", "fastapi", "react", "mongodb", "python", "docker")),
      "no resume keyword found in questions")
check("no greeting/introduction in any question",
      not any(q.lower().lstrip("[").startswith(("hello", "hi ", "welcome", "i am your", "i'm your"))
              for q in questions), "")
check("no invented technology claims (Java/Spring absent from resume)",
      "spring" not in joined.lower() and not re.search(r"\bjava\b", joined.lower()),
      "LLM invented tech not present in the resume")

# --- 6. full lifecycle: save one answer turn, then evaluate ---
r = client.post("/api/interview/answer", json={
    "session_id": sid, "user_id": UID, "question_index": 0,
    "answer": "In MedVision AI I designed the FastAPI layer with async endpoints "
              "and used MongoDB grids for DICOM metadata.",
})
check("save answer turn -> 200", r.status_code == 200, f"status={r.status_code}")

r = client.post("/api/interview/evaluate", json={
    "session_id": sid, "user_id": UID,
    "questions": questions,
    "answers": ["answer"] * len(questions),
})
check("evaluate -> 200", r.status_code == 200, f"status={r.status_code} body={str(r.get_json())[:120]}")
check("evaluation produced a numeric score",
      isinstance((r.get_json() or {}).get("score"), (int, float)),
      str((r.get_json() or {}).get("score")))

# --- 7. cleanup ---
users_collection.delete_one({"_id": uid})
if sid:
    submissions_collection.delete_many({"_id": __import__("bson").ObjectId(sid)})
fname = user.get("resume_filename")
if fname:
    p = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    if os.path.exists(p):
        os.remove(p)

print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("E2E (RESUME GATE + OLLAMA 40/40/20 QUESTIONS) PASSED")
