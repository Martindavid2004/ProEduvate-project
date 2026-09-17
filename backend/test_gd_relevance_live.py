"""Live verification test for the GD topic-relevance fixes.

Verifies (against a RUNNING backend on 127.0.0.1:5000):
  1. POST /gd/agent-response with an OFF-TOPIC latest_user_text returns
     "This is not related to the topic. Please speak points related to the topic."
  2. POST /gd/agent-response with an ON-TOPIC latest_user_text returns a
     discussion point (NOT the rejection sentence).
  3. A GD round whose stored speech is OFF-TOPIC evaluates with
     topic_related=false, every criterion score <= 5, total <= 5 (near zero),
     and per-criterion feedback present.
  4. A control ON-TOPIC round evaluates with normal scores and evidence/reason
     quotes visible in criterion_feedback.
"""
import sys
import time
import uuid

import requests

BASE = "http://127.0.0.1:5000/api"
REJECT_SENTENCE = "This is not related to the topic. Please speak points related to the topic."

results = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((status, name))
    print(f"[{status}] {name}" + (f" -> {detail}" if detail else ""))


# ---------- Auth ----------
email = f"gdreltest_{uuid.uuid4().hex[:8]}@test.com"
r = requests.post(f"{BASE}/auth/register", json={
    "fullName": "GD Relevance Tester", "registerNumber": f"GD{uuid.uuid4().hex[:6]}",
    "email": email, "department": "CSE", "password": "test1234"
})
d = r.json()
token = d.get("token", "")
user_id = str(d.get("user", {}).get("id", ""))
check("register test student", r.status_code == 201 and bool(token), str(d)[:120])
H = {"Authorization": f"Bearer {token}"}
if not token:
    sys.exit(1)

TOPIC = "Impact of Artificial Intelligence on Employment"

# ---------- 1. Agent responds to OFF-TOPIC speech ----------
print("\n--- AGENT: off-topic speech ---")
r = requests.post(f"{BASE}/gd/agent-response", headers=H, json={
    "topic": TOPIC,
    "context": "You: I love playing cricket with my friends every Sunday morning.",
    "agent_personality": "analytical",
    "agent_gender": "male",
    "latest_user_text": "I love playing cricket with my friends every Sunday morning and we eat pizza after the match.",
})
d = r.json()
resp = str(d.get("response", ""))
check("agent-response HTTP 200", r.status_code == 200, f"status={r.status_code}")
check(
    "OFF-TOPIC speech -> agent says 'not related to the topic'",
    "not related to the topic" in resp.lower(),
    f"resp={resp[:140]!r}"
)
check(
    "OFF-TOPIC speech -> off_topic_reply flag is True",
    d.get("off_topic_reply") is True,
    f"off_topic_reply={d.get('off_topic_reply')}"
)

# ---------- 2. Agent responds to ON-TOPIC speech ----------
print("\n--- AGENT: on-topic speech ---")
on_topic = ("AI will automate routine jobs but it also creates new roles in data science "
            "and machine learning, so the workforce must be reskilled.")
r = requests.post(f"{BASE}/gd/agent-response", headers=H, json={
    "topic": TOPIC,
    "context": f"You: {on_topic}",
    "agent_personality": "diplomatic",
    "agent_gender": "female",
    "latest_user_text": on_topic,
})
d = r.json()
resp = str(d.get("response", ""))
check("agent-response HTTP 200 (on-topic)", r.status_code == 200, f"status={r.status_code}")
check(
    "ON-TOPIC speech -> agent engages (no rejection sentence)",
    "not related to the topic" not in resp.lower() and len(resp) > 10,
    f"resp={resp[:140]!r}"
)
check(
    "ON-TOPIC speech -> off_topic_reply flag is False",
    d.get("off_topic_reply") is False,
    f"off_topic_reply={d.get('off_topic_reply')}"
)


def run_round(title, text):
    r = requests.post(f"{BASE}/gd/practice-round", headers=H, json={
        "title": title, "num_ai_agents": 5, "topic": TOPIC,
        "allow_topic_selection": False, "duration": 1
    })
    d = r.json()
    round_id = d.get("gd_round", {}).get("_id", "")
    assert round_id, str(d)[:200]
    requests.post(f"{BASE}/gd/round/{round_id}/start", headers=H)
    requests.post(f"{BASE}/gd/round/{round_id}/submit-response", headers=H, json={
        "response_text": text, "duration": 30
    })
    t0 = time.time()
    r = requests.post(f"{BASE}/gd/round/{round_id}/evaluate", headers=H)
    latency = time.time() - t0
    return r.json().get("results", {}), latency


# ---------- 3. OFF-TOPIC round evaluation ----------
print("\n--- EVAL: off-topic round ---")
off_topic_text = ("I love playing cricket with my friends every Sunday morning. "
                  "We ate pizza after the match and watched a movie in the evening. "
                  "The weather was really nice that day.")
res, latency = run_round("Relevance Test OFF-TOPIC", off_topic_text)
me = next((p for p in res.get("all_participants", []) if p.get("type") == "student"), {})
scores = me.get("scores", {})
max_crit = max((v.get("score", 0) for v in scores.values()), default=-1)
total = me.get("total_score", -1)
print(f"    topic_related={res.get('topic_related')} method={res.get('evaluation_method')}")
print(f"    scores={ {k: v.get('score') for k, v in scores.items()} } total={total}")
check("OFF-TOPIC: topic_related is False", res.get("topic_related") is False)
check("OFF-TOPIC: every criterion score <= 5", 0 <= max_crit <= 5, f"max_criterion={max_crit}")
check("OFF-TOPIC: total score near zero (<= 5)", 0 <= total <= 5, f"total={total}")
fb = res.get("criterion_feedback", {})
check(
    "OFF-TOPIC: per-criterion feedback present with a reason",
    bool(fb) and all(str(v.get("reason", "")).strip() for v in fb.values()),
    f"feedback_keys={list(fb.keys())[:3]} sample={str(list(fb.values())[:1])[:160]}"
)

# ---------- 4. ON-TOPIC control round ----------
print("\n--- EVAL: on-topic control round ---")
on_topic_text = ("I believe AI will create more jobs than it destroys because automation boosts "
                 "productivity and creates entirely new industries. Workers displaced from routine "
                 "roles can be reskilled for data science and machine learning careers, so "
                 "employment will shift rather than disappear.")
res2, latency2 = run_round("Relevance Test ON-TOPIC", on_topic_text)
me2 = next((p for p in res2.get("all_participants", []) if p.get("type") == "student"), {})
scores2 = me2.get("scores", {})
total2 = me2.get("total_score", -1)
print(f"    topic_related={res2.get('topic_related')} method={res2.get('evaluation_method')}")
print(f"    scores={ {k: v.get('score') for k, v in scores2.items()} } total={total2}")
check("ON-TOPIC: topic_related is True", res2.get("topic_related") is True)
check("ON-TOPIC: total score is a real score (>= 30)", total2 >= 30, f"total={total2}")
fb2 = res2.get("criterion_feedback", {})
has_evidence_or_reason = any(
    (v.get("evidence") and v.get("evidence").lower() != "none") or v.get("reason")
    for v in fb2.values()
)
check(
    "ON-TOPIC: evidence/reason quotes returned in criterion_feedback",
    has_evidence_or_reason,
    f"sample={str(list(fb2.values())[:1])[:200]}"
)

# ---------- Summary ----------
passed = sum(1 for s, _ in results if s == "PASS")
failed = sum(1 for s, _ in results if s == "FAIL")
print(f"\n{'='*60}\nSUMMARY: {passed} passed, {failed} failed\n{'='*60}")
for s, n in results:
    print(f"  [{s}] {n}")
sys.exit(1 if failed else 0)
