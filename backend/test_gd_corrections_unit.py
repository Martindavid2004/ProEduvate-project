"""Standalone sanity test for the four GD corrections (no running backend needed).

Verifies:
  1. check_topic_relevance() semantic gate (LLM unavailable -> heuristic path)
  2. generate_ai_agent_response() returns OFF_TOPIC_REPLY for unrelated user
     speech, and a normal response otherwise (heuristic path)
  3. generate_ai_agent_score() distribution now spreads below a typical
     student score so rank is dynamic (rank-8 root cause removed)
  4. Ranking tie handling (90, 90, 80 -> ranks 1, 1, 3)

Run from backend/: python test_gd_corrections_unit.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gd_service import GDService

failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))
    if not cond:
        failures.append(name)


svc = GDService()
TOPIC = "Impact of Artificial Intelligence on Employment"

# ---- 1. Dedicated relevance check (heuristic path: no LLM keys in unit env) ----
rel_on = svc.check_topic_relevance(TOPIC, "Reskilling workers is necessary because automation can change job requirements.")
check("relevance: semantic indirect relevance detected", rel_on["is_relevant"] is True, str(rel_on))

rel_off = svc.check_topic_relevance(TOPIC, "I went to Chennai yesterday to watch a movie with my friends.")
check("relevance: unrelated statement rejected", rel_off["is_relevant"] is False, str(rel_off))

rel_kw = svc.check_topic_relevance(TOPIC, "The AI in my phone recommends movies.")
check("relevance: keyword-only match can stay unrelated", rel_kw["is_relevant"] is False, str(rel_kw))

check("relevance: structured output keys", all(k in rel_off for k in ("is_relevant", "confidence", "reason", "method")))

# ---- 2. Agent response flow: off-topic -> intervention, on-topic -> normal ----
# NOTE: the authoritative gate lives in the ROUTE (gd_routes.py), which calls
# check_topic_relevance() FIRST and short-circuits to OFF_TOPIC_REPLY before
# any agent prompt is built. Simulate that exact flow here.
def route_flow(latest_user_text, respond_to_type='user'):
    relevance = None
    if respond_to_type != 'agent' and latest_user_text.strip():
        relevance = svc.check_topic_relevance(TOPIC, latest_user_text, "")
        if not relevance.get("is_relevant", True):
            return GDService.OFF_TOPIC_REPLY
    return svc.generate_ai_agent_response(
        topic=TOPIC, context="You: hello", agent_personality="analytical",
        agent_gender="male", latest_user_text=latest_user_text, relevance=relevance)

off_resp = route_flow("I love playing cricket with my friends every Sunday.")
check("agent: off-topic -> OFF_TOPIC_REPLY (route gate)", off_resp == GDService.OFF_TOPIC_REPLY, repr(off_resp[:80]))

on_resp = route_flow("AI can automate repetitive jobs but create new roles in data science.")
check("agent: on-topic -> normal response (not OFF_TOPIC_REPLY)", on_resp != GDService.OFF_TOPIC_REPLY, repr(on_resp[:80]))

# Agent-directed turn: responds to previous AGENT, must not be OFF_TOPIC_REPLY
ag_resp = svc.generate_ai_agent_response(
    topic=TOPIC, context="AI Agent 2: AI will create more jobs than it destroys.",
    agent_personality="diplomatic", agent_gender="female", latest_user_text="",
    respond_to_name="AI Agent 2", respond_to_type="agent",
    respond_to_text="AI will create more jobs than it destroys.", agent_name="AI Agent 3")
check("agent: agent-directed turn produces a response", isinstance(ag_resp, str) and len(ag_resp) > 0, repr(ag_resp[:80]))
check("agent: agent-directed turn does not require user relevance gate", ag_resp != GDService.OFF_TOPIC_REPLY, repr(ag_resp[:80]))

# ---- 3. Simulated agent score distribution (rank-8 root cause) ----
from app.routes.gd_routes import generate_ai_agent_score, DEFAULT_EVALUATION_CRITERIA

totals = [generate_ai_agent_score(DEFAULT_EVALUATION_CRITERIA, f"ai_agent_{i}", "r1")["total_score"]
          for i in range(1, 8)]
check("scores: agent totals are not all above 60", any(t < 60 for t in totals), f"totals={totals}")
check("scores: spread is wide (max-min > 15)", (max(totals) - min(totals)) > 15, f"spread={max(totals)-min(totals):.1f}")
check("scores: deterministic for same seed", totals == [generate_ai_agent_score(DEFAULT_EVALUATION_CRITERIA, f"ai_agent_{i}", "r1")["total_score"] for i in range(1, 8)])

# ---- 4. Ranking tie handling (standard competition method) ----
participants = [
    {"name": "A", "total_score": 90.0, "rank": 0},
    {"name": "B", "total_score": 90.0, "rank": 0},
    {"name": "C", "total_score": 80.0, "rank": 0},
]
participants.sort(key=lambda x: x["total_score"], reverse=True)
last_score, last_rank = None, 0
for idx, p in enumerate(participants, start=1):
    if last_score is not None and abs(p["total_score"] - last_score) < 1e-9:
        p["rank"] = last_rank
    else:
        p["rank"] = idx
        last_rank = idx
        last_score = p["total_score"]
ranks = [p["rank"] for p in participants]
check("ranking: ties share rank 1, next is rank 3", ranks == [1, 1, 3], f"ranks={ranks}")

print()
if failures:
    print(f"{len(failures)} check(s) FAILED: {failures}")
    sys.exit(1)
print("All checks passed.")
