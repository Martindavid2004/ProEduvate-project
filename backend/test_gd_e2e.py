"""End-to-end test for the GD (Group Discussion) system."""
import io
import json
import os
import struct
import time
import uuid
import wave
import requests
import sys

BASE = "http://127.0.0.1:5000/api"
results = []
failures = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name}" + (f" -> {detail}" if detail else ""))

def section(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

# ---------- 1. Register a test student ----------
section("AUTH")
email = f"gdtester_{uuid.uuid4().hex[:8]}@test.com"
r = requests.post(f"{BASE}/auth/register", json={
    "fullName": "GD Tester", "registerNumber": f"GD{uuid.uuid4().hex[:6]}",
    "email": email, "department": "CSE", "password": "test1234"
})
tok_data = r.json()
check("register student", r.status_code == 201 and tok_data.get("success"), str(tok_data)[:200])
token = tok_data.get("token", "")
user_id = str(tok_data.get("user", {}).get("id", ""))
H = {"Authorization": f"Bearer {token}"}

if not token:
    print("Cannot continue without token"); sys.exit(1)

# ---------- 2. Topics & criteria ----------
section("TOPICS / CRITERIA")
r = requests.get(f"{BASE}/gd/topics", headers=H)
d = r.json()
check("GET /gd/topics", r.status_code == 200 and d.get("success") and len(d.get("topics", [])) > 0, f"{len(d.get('topics', []))} topics")
topic = d["topics"][0]

r = requests.get(f"{BASE}/gd/evaluation-criteria", headers=H)
d = r.json()
check("GET /gd/evaluation-criteria", r.status_code == 200 and d.get("success") and "communication_skills" in d.get("criteria", {}), str(d)[:150])

# ---------- 3. Create practice round ----------
section("PRACTICE ROUND")
r = requests.post(f"{BASE}/gd/practice-round", headers=H, json={
    "title": "E2E Practice GD", "num_ai_agents": 5, "topic": topic,
    "allow_topic_selection": False, "duration": 1
})
d = r.json()
check("POST /gd/practice-round", r.status_code == 201 and d.get("success"), str(d)[:200])
round_id = d.get("gd_round", {}).get("_id", "")

# ---------- 4. LLM agent response (llama via Ollama / Gemini) ----------
section("AI AGENT RESPONSE (LLM)")
t0 = time.time()
r = requests.post(f"{BASE}/gd/agent-response", headers=H, json={
    "topic": topic, "context": "Opening statement by the student about the topic.",
    "agent_personality": "analytical", "agent_gender": "male"
})
latency = time.time() - t0
d = r.json()
resp_text = d.get("response", "")
check("POST /gd/agent-response", r.status_code == 200 and d.get("success") and len(resp_text) > 5, f"latency={latency:.2f}s resp={resp_text[:80]!r}")
if latency > 10:
    check("agent-response latency < 10s", False, f"took {latency:.2f}s")

# ---------- 7. Speech-to-text (offline Whisper fallback) ----------
section("SPEECH-TO-TEXT (Whisper)")

def make_wav_bytes(duration_s=2.0, freq_hz=440.0, rate=16000):
    """Generate a small mono 16-bit PCM WAV in memory (a 440Hz tone)."""
    buf = io.BytesIO()
    n = int(duration_s * rate)
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b''.join(
            struct.pack('<h', int(12000 * __import__('math').sin(2 * 3.141592653589793 * freq_hz * i / rate)))
            for i in range(n)
        ))
    return buf.getvalue()

wav_bytes = make_wav_bytes()
r = requests.post(
    f"{BASE}/gd/transcribe", headers=H,
    files={"audio": ("recording.wav", wav_bytes, "audio/wav")}
)
d = r.json()
check("POST /gd/transcribe (real audio file)", r.status_code == 200 and d.get("success") is True, f"status={r.status_code} text={d.get('text','')!r:.80}")

# Missing file -> 400
r = requests.post(f"{BASE}/gd/transcribe", headers=H)
check("POST /gd/transcribe without file -> 400", r.status_code == 400, f"status={r.status_code}")

# Empty-content file -> 400 error (meaningful error message)
r = requests.post(
    f"{BASE}/gd/transcribe", headers=H,
    files={"audio": ("recording.wav", b"", "audio/wav")}
)
d = r.json()
check("POST /gd/transcribe empty file -> 400 error", r.status_code == 400 and d.get("success") is False and "error" in d, f"status={r.status_code} error={d.get('error','')!r}")


# ---------- 8. Start round ----------
section("START ROUND")
r = requests.post(f"{BASE}/gd/round/{round_id}/start", headers=H)
check("POST /gd/round/<id>/start", r.status_code == 200, str(r.json())[:150])

# ---------- 9. Submit response ----------
section("SUBMIT RESPONSE")
r = requests.post(f"{BASE}/gd/round/{round_id}/submit-response", headers=H, json={
    "response_text": "I believe AI will create more jobs than it destroys because it boosts productivity and creates new industries. We must invest in reskilling programs to prepare the workforce for these changes.",
    "duration": 45
})
check("POST /gd/round/<id>/submit-response", r.status_code == 200, str(r.json())[:150])

# ---------- 10. Get rounds list ----------
section("ROUNDS LISTING")
r = requests.get(f"{BASE}/gd/rounds", headers=H)
d = r.json()
check("GET /gd/rounds", r.status_code == 200 and d.get("success") and len(d.get("rounds", [])) >= 1, f"{len(d.get('rounds', []))} rounds")

# ---------- 11. Evaluate round ----------
section("EVALUATE")
t0 = time.time()
r = requests.post(f"{BASE}/gd/round/{round_id}/evaluate", headers=H)
latency = time.time() - t0
d = r.json()
ok = r.status_code == 200 and d.get("success") and d.get("results", {}).get("student_rank") is not None
check("POST /gd/round/<id>/evaluate", ok, f"latency={latency:.2f}s rank={d.get('results',{}).get('student_rank') if ok else str(d)[:150]}")
if latency > 15:
    check("evaluate latency < 15s", False, f"took {latency:.2f}s")

# ---------- 12. Results ----------
section("RESULTS")
r = requests.get(f"{BASE}/gd/results/{user_id}", headers=H)
d = r.json()
check("GET /gd/results/<id>", r.status_code == 200 and d.get("success") and len(d.get("results", [])) >= 1, f"{len(d.get('results', []))} results")

# ---------- 13. Authorization checks ----------
section("AUTH CHECKS")
r = requests.get(f"{BASE}/gd/topics")
check("GD endpoint without token rejected", r.status_code == 401, f"status={r.status_code}")

# ---------- Summary ----------
print(f"\n{'='*60}\nSUMMARY: {sum(1 for s,_,_ in results if s=='PASS')} passed, {sum(1 for s,_,_ in results if s=='FAIL')} failed\n{'='*60}")
for s, n, d in results:
    print(f"  [{s}] {n} {('-> '+d) if d else ''}")
sys.exit(1 if any(s == "FAIL" for s, _, _ in results) else 0)