"""One-off live TEST 1: resume-based interview question generation.

Flow (real Flask app, real MongoDB Atlas, real Gemini):
  1. create throwaway student
  2. generate a PDF resume mentioning 'MedVision AI - FastAPI, React, MongoDB'
  3. POST /api/student/<uid>/upload_resume  -> resume_text persisted
  4. POST /api/interview/start              -> questions reference the resume
  5. cleanup (user, sessions, uploaded file)

Run:  cd backend && ../backend/venv/Scripts/python.exe _tmp_test1_resume_flow.py
"""
import io
import os
import sys
import uuid

import fitz  # PyMuPDF

from app import create_app
from app.database import users_collection, submissions_collection

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

# 1. throwaway user
suffix = uuid.uuid4().hex[:8]
uid = users_collection.insert_one({
    "name": f"ResumeE2E {suffix}",
    "email": f"resume_e2e_{suffix}@test.local",
    "role": "student",
}).inserted_id
UID = str(uid)

# 2. build the PDF
pdf = fitz.open()
page = pdf.new_page()
y = 60
for line in RESUME_LINES:
    page.insert_text((50, y), line, fontsize=11)
    y += 20
buf = pdf.tobytes()
pdf.close()

# 3. upload resume
r = client.post(f"/api/student/{UID}/upload_resume", data={
    "resume": (io.BytesIO(buf), "jane_doe_resume.pdf"),
}, content_type="multipart/form-data")
check("upload resume -> 200", r.status_code == 200, f"status={r.status_code} body={str(r.get_json())[:120]}")
check("ATS score returned", isinstance(r.get_json().get("match_score"), (int, float)),
      str(r.get_json().get("match_score")))

user = users_collection.find_one({"_id": uid})
check("resume_text persisted on user",
      "MedVision AI" in (user.get("resume_text") or ""),
      f"chars={len(user.get('resume_text') or '')}")
check("resume_filename stored", bool(user.get("resume_filename")), user.get("resume_filename"))

# 4. start interview -> questions must reference the resume
print("\n--- backend logs (interview start) ---")
r = client.post("/api/interview/start", json={"user_id": UID, "mode": "text"})
check("start interview -> 200", r.status_code == 200, f"status={r.status_code}")
data = r.get_json()
questions = data.get("questions") or []
sid = (data.get("session") or {}).get("sessionId")
print(f"--- {len(questions)} questions generated ---")
for i, q in enumerate(questions[:5], 1):
    print(f"  Q{i}: {q}")

joined = " ".join(questions).lower()
check("10 questions generated", len(questions) == 10, f"n={len(questions)}")
check("a question references the resume project/skills",
      any(k in joined for k in ("medvision", "fastapi", "react", "mongodb")),
      "no resume keyword found in questions")
check("no greeting/introduction in any question",
      not any(q.lower().startswith(("hello", "hi ", "welcome", "i am your", "i'm your"))
              for q in questions))
check("no invented technology claims (Java/C++ absent from resume)",
      not any(k in joined for k in ("your experience with java,", "your c++ project", "spring boot project")),
      "")

# cleanup
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
print("TEST 1 (RESUME-BASED QUESTIONS) PASSED")
