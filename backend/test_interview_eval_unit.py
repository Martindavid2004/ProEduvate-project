# test_interview_eval_unit.py
"""
Unit tests for the evidence-based interview evaluation (interview_service).

Covers the exact scenarios from the task spec:
  TEST 1 - relevant answer scores appropriately (no fabricated evidence)
  TEST 2 - irrelevant answer -> IRRELEVANT, ~0 content score, honest feedback
  TEST 3 - empty speech -> NO_ANSWER, no positive score, retry message path
  plus: weighted-total arithmetic, LOW_CONFIDENCE capping, '0 valid answers
  across 10 questions' final-score honesty, and the old bug regression
  (13x 'No answer provided' must NOT yield ~67-69).

Run:  cd backend && ../.venv/Scripts/python.exe test_interview_eval_unit.py
(No database / network needed.)
"""
import sys

from app.services.interview_service import (
    evaluate_interview, classify_relevance, EVALUATION_WEIGHTS,
    RELEVANT, PARTIALLY_RELEVANT, IRRELEVANT, NO_ANSWER,
)

failures = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        failures.append(f"{name}: {detail}")


Q = "What is your experience with React?"

# ---------------------------------------------------------------------------
# TEST 1 - relevant answer
# ---------------------------------------------------------------------------
res = classify_relevance(Q, "I worked on a React project where I built reusable components and used hooks.")
check("T1 relevance classification", res['classification'] in (RELEVANT, PARTIALLY_RELEVANT),
      res['classification'])
check("T1 relevance detected topical overlap", res['overlap'] >= 1, f"overlap={res['overlap']}")

r1 = evaluate_interview([{'question': Q,
                          'answer': "I worked on a React project where I built reusable components and used hooks."}])
d1 = r1['details'][0]
check("T1 content score clearly positive", d1['scores']['content_relevance'] >= 50,
      f"content={d1['scores']['content_relevance']}")
check("T1 technical evidence quotes actual speech", 'React' in d1['evidence']['technical_depth']
      or 'react' in d1['evidence']['technical_depth'].lower(),
      d1['evidence']['technical_depth'][:80])
check("T1 final score in normal band", 20 <= r1['score'] <= 85, f"score={r1['score']}")
check("T1 no fabricated leadership claim", r1['criteria_averages']['leadership'] <= 40,
      f"leadership={r1['criteria_averages']['leadership']}")

# ---------------------------------------------------------------------------
# TEST 2 - irrelevant answer
# ---------------------------------------------------------------------------
res2 = classify_relevance(Q, "I went to the beach yesterday and watched a movie.")
check("T2 classified IRRELEVANT", res2['classification'] == IRRELEVANT, res2['classification'])

r2 = evaluate_interview([{'question': Q,
                          'answer': "I went to the beach yesterday and watched a movie with my friends, it was a really nice day outside."}])
d2 = r2['details'][0]
check("T2 detail classified IRRELEVANT", d2['classification'] == IRRELEVANT, d2['classification'])
check("T2 content score is zero", d2['scores']['content_relevance'] == 0,
      f"content={d2['scores']['content_relevance']}")
check("T2 technical score is zero", d2['scores']['technical_depth'] == 0,
      f"technical={d2['scores']['technical_depth']}")
check("T2 reason says it does not address the question",
      'does not address the question' in d2['relevance_reason'], d2['relevance_reason'])
check("T2 total score very low", r2['score'] <= 15, f"score={r2['score']}")
check("T2 feedback counts the irrelevant answer",
      'unrelated' in r2['feedback'] or 'irrelevant' in r2['feedback'].lower(),
      r2['feedback'][:120])

# ---------------------------------------------------------------------------
# TEST 3 - empty / no speech
# ---------------------------------------------------------------------------
res3 = classify_relevance(Q, "")
check("T3 empty classified NO_ANSWER", res3['classification'] == NO_ANSWER, res3['classification'])

r3 = evaluate_interview([{'question': Q, 'answer': ''}])
d3 = r3['details'][0]
check("T3 all criterion scores zero", all(v == 0 for v in d3['scores'].values()), str(d3['scores']))
check("T3 total score zero", r3['score'] == 0, f"score={r3['score']}")
check("T3 valid_answers = 0", r3['stats']['valid_answers'] == 0, str(r3['stats']))

# Low-confidence: stored but capped
r3b = evaluate_interview([{'question': Q, 'answer': 'I used react hooks',
                           'transcript_status': 'LOW_CONFIDENCE'}])
d3b = r3b['details'][0]
check("T3b LOW_CONFIDENCE capped to PARTIALLY_RELEVANT",
      d3b['classification'] == PARTIALLY_RELEVANT, d3b['classification'])
check("T3b LOW_CONFIDENCE content score limited", d3b['scores']['content_relevance'] <= 45,
      f"content={d3b['scores']['content_relevance']}")

# ---------------------------------------------------------------------------
# Spec section A7/C1 - 0 meaningful answers across 10 questions
# ---------------------------------------------------------------------------
empty_transcript = [{'question': f"Question {i}?", 'answer': ''} for i in range(10)]
r4 = evaluate_interview(empty_transcript)
check("A7 ten empty answers -> score 0", r4['score'] == 0, f"score={r4['score']}")
check("A7 feedback states no valid answers",
      'No valid substantive answers' in r4['feedback'], r4['feedback'][:100])
check("A7 no 'strong enthusiasm' phrasing", 'strong enthusiasm' not in r4['feedback'])

# ---------------------------------------------------------------------------
# Regression: the old production bug (13x 'No answer provided' -> 67)
# ---------------------------------------------------------------------------
r5 = evaluate_interview([{'question': f"Question {i}?", 'answer': 'No answer provided'}
                         for i in range(13)])
check("REG 13x 'No answer provided' -> score 0", r5['score'] == 0, f"score={r5['score']}")
check("REG no 'strong enthusiasm'", 'strong enthusiasm' not in r5['feedback'])
check("REG stats show 13 missing", r5['stats']['no_answer_count'] == 13, str(r5['stats']))

# ---------------------------------------------------------------------------
# Spec section C - weighted arithmetic: total == sum of weighted contributions
# ---------------------------------------------------------------------------
r6 = evaluate_interview([
    {'question': Q, 'answer': "I worked on a React project where I created reusable components, "
                              "used hooks and state management, and improved rendering performance "
                              "by 40% for our customers because the dashboard was slow before."},
])
d6 = r6['details'][0]
recomputed = round(sum(d6['scores'][k] * (w / 100.0) for k, w in EVALUATION_WEIGHTS.items()), 2)
check("C weighted contribution = sum(score x weight)",
      abs(d6['weighted_contribution'] - recomputed) < 0.01,
      f"stored={d6['weighted_contribution']} recomputed={recomputed}")
check("C final score == mean of per-turn weighted contributions",
      abs(r6['score'] - round(d6['weighted_contribution'], 2)) < 0.011,
      f"final={r6['score']} turn={d6['weighted_contribution']}")
check("C metric evidence extracted from actual speech", '40%' in (d6['evidence']['technical_depth'] or ''),
      d6['evidence']['technical_depth'][:100])

# ---------------------------------------------------------------------------
# Single-word transcript (STT LOW_CONFIDENCE case)
# ---------------------------------------------------------------------------
r7 = evaluate_interview([{'question': Q, 'answer': 'yes'}])
check("single word 'yes' scores near zero", r7['score'] <= 10, f"score={r7['score']}")

# ---------------------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("ALL UNIT TESTS PASSED")
