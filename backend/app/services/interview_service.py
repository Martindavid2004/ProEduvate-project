# interview_service.py
"""
Evidence-based Mock Interview evaluation.

Core contract: EVERY score, evidence line and feedback sentence must be
traceable to what the candidate ACTUALLY said (or did not say). The evaluator
never invents positive evidence and never awards a normal score for an empty,
unrelated or missing answer.

Scoring model (weights sum to 100):

    content_relevance   20%
    communication       25%
    technical_depth     20%
    leadership          15%
    listening           10%
    logical_reasoning   10%

Each criterion gets a 0-100 score derived ONLY from the transcript, then the
final score is the sum of the weighted contributions (criterion x weight%),
rounded to 2 decimals. Weighted contributions are reported separately from
criterion scores so the two can never be confused.
"""

import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Evaluation weights (must sum to 100)
# ---------------------------------------------------------------------------
EVALUATION_WEIGHTS = {
    'content_relevance': 20,
    'communication': 25,
    'technical_depth': 20,
    'leadership': 15,
    'listening': 10,
    'logical_reasoning': 10,
}
assert sum(EVALUATION_WEIGHTS.values()) == 100

# Relevance classifications
RELEVANT = 'RELEVANT'
PARTIALLY_RELEVANT = 'PARTIALLY_RELEVANT'
IRRELEVANT = 'IRRELEVANT'
NO_ANSWER = 'NO_ANSWER'

# Pass mark for the mock interview: the final score must reach this value for
# a PASS status. Exposed in the result so the UI/dashboard never re-derives it.
# Set to 60% (user decision): a stricter placement-readiness bar than the
# original 50% - average performances fail, strong ones pass.
PASS_MARK = 60.0

# Words that carry no topical meaning when matching question<->answer
_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'so', 'of', 'to', 'in',
    'on', 'at', 'by', 'for', 'with', 'about', 'as', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'am', 'do', 'does', 'did', 'have', 'has', 'had',
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it', 'its',
    'they', 'them', 'their', 'this', 'that', 'these', 'those', 'there', 'here',
    'what', 'which', 'who', 'whom', 'how', 'when', 'where', 'why', 'will',
    'would', 'can', 'could', 'should', 'shall', 'may', 'might', 'must',
    'very', 'really', 'just', 'also', 'too', 'some', 'any', 'more', 'most',
    'much', 'many', 'lot', 'lots', 'like', 'well', 'okay', 'yes', 'no', 'not',
    'think', 'thought', 'feel', 'felt', 'say', 'said', 'tell', 'told',
    'good', 'great', 'nice', 'fine', 'better', 'best', 'thing', 'things',
    'something', 'anything', 'everything', 'nothing', 'one', 'two', 'three',
}

# Interview filler/lead-ins that add no substance
_FILLER_STARTS = re.compile(
    r"^(well|okay|ok|so|yeah|yep|um+|uh+|hmm+|like|actually|basically)\b[,\s]*",
    re.IGNORECASE,
)


def _words(text):
    return re.findall(r"[a-z0-9+#.]+", (text or '').lower())


def _content_words(text):
    """Words minus stopwords - the terms that can carry topical meaning."""
    return [w for w in _words(text) if w not in _STOPWORDS and len(w) > 1]


def _meaningful(text):
    """A transcript is meaningful when it has enough real content words."""
    return len(_content_words(text)) >= 3


def _strip_filler(text):
    cleaned = (text or '').strip()
    prev = None
    while prev != cleaned:
        prev = cleaned
        cleaned = _FILLER_STARTS.sub('', cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Transcript status handling (from the STT pipeline)
# ---------------------------------------------------------------------------

def resolve_transcript_entry(item):
    """Classify one interview turn as usable speech or not.

    Returns (answer_text, status) where status is one of:
      'no_answer'      - nothing usable was said (empty/whitespace)
      'low_confidence' - STT flagged the transcript as LOW_CONFIDENCE
      'ok'             - transcript present and not flagged
    """
    answer = (item.get('answer') or '').strip() if isinstance(item, dict) else ''
    stt_status = (item.get('transcript_status') or item.get('status') or '').upper()
    if not answer:
        return '', 'no_answer'
    if stt_status == 'LOW_CONFIDENCE':
        return answer, 'low_confidence'
    return answer, 'ok'


# ---------------------------------------------------------------------------
# Question <-> answer topic relevance
# ---------------------------------------------------------------------------

def _topic_terms(question):
    """Topical terms of the question: content words + skill/tech keywords.

    Skill keywords (react, python, sql, ...) are kept even though some are
    short, because they are exactly what interview questions are about.
    """
    known_skills = {
        'react', 'java', 'python', 'javascript', 'node', 'node.js', 'spring',
        'sql', 'mongodb', 'postgresql', 'mysql', 'docker', 'aws', 'git',
        'rest', 'api', 'api', 'c++', 'c#', 'typescript', 'flask', 'django',
        'html', 'css', 'machine', 'learning', 'data', 'structures',
        'algorithms', 'leadership', 'teamwork', 'agile', 'testing', 'devops',
        'kubernetes', 'linux', 'system', 'design', 'microservices',
    }
    terms = set()
    for w in _content_words(question):
        terms.add(w)
    for w in _words(question):
        if w in known_skills:
            terms.add(w)
    return terms


def _answer_terms(answer):
    return set(_content_words(answer))


def classify_relevance(question, answer):
    """Classify how well the answer addresses the question.

    Returns dict:
        classification: RELEVANT | PARTIALLY_RELEVANT | IRRELEVANT | NO_ANSWER
        overlap:        number of shared topical terms
        reason:         human-readable justification grounded in the two texts
    """
    answer_stripped = _strip_filler(answer)
    if not answer_stripped or not _meaningful(answer_stripped):
        return {
            'classification': NO_ANSWER,
            'overlap': 0,
            'reason': 'No usable answer content was provided for this question.',
        }

    topic_terms = _topic_terms(question)
    answer_terms = _answer_terms(answer_stripped)
    overlap = topic_terms & answer_terms

    if overlap:
        classification = RELEVANT
        reason = ('Answer addresses the question topic '
                  f"({', '.join(sorted(overlap)[:5])}).")
    else:
        # No lexical overlap: for interviews (where the question directly
        # frames what the answer must contain) zero shared topical terms
        # strongly indicates an unrelated answer. Distinguish "mentions the
        # question area but too briefly" from "talks about something else".
        q_words = set(_content_words(question))
        # partial: answer shares ANY word (even non-topical) with the question
        answer_all = set(_words(answer_stripped))
        loose = q_words & answer_all
        if loose:
            classification = PARTIALLY_RELEVANT
            reason = ('Answer only loosely touches the question; it does not '
                      'clearly address what was asked.')
        else:
            classification = IRRELEVANT
            reason = ('Answer does not address the question; it discusses an '
                      'unrelated topic.')

    return {
        'classification': classification,
        'overlap': len(overlap),
        'reason': reason,
    }


# ---------------------------------------------------------------------------
# Criterion scoring (grounded in the transcript)
# ---------------------------------------------------------------------------

def _find_evidence(answer, patterns):
    """Return the first transcript snippet matching any pattern, else None."""
    for pat in patterns:
        m = re.search(pat, answer, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 40)
            end = min(len(answer), m.end() + 60)
            snippet = answer[start:end].strip()
            prefix = '...' if start > 0 else ''
            suffix = '...' if end < len(answer) else ''
            return f'"{prefix}{snippet}{suffix}"'
    return None


# Patterns extract evidence ONLY when the candidate actually said it.
_TECH_EVIDENCE = [
    r'\b(built|developed|created|designed|implemented|worked on|made)\b',
    r'\b(project|application|app|website|api|feature|component|system)\b',
    r'\b(react|python|java|javascript|node|sql|database|docker|aws|api)\b',
    r'\b(hooks|redux|state|props|component|rest|graphql|microservice)\b',
]
_TEAM_EVIDENCE = [
    r'\b(team|led|mentored|mentoring|coordinated|organized|managed|guided)\b',
    r'\b(lead|leader|leadership|delegated|reviewed|onboarded)\b',
]
_LISTEN_EVIDENCE = [
    r'\b(listened|feedback|collaborat|colleague|coworker|pair|discussed)\b',
    r'\b(question asked|clarif|understood the requirement)\b',
]
_REASON_EVIDENCE = [
    r'\b(because|therefore|so that|as a result|which led|due to)\b',
    r'\b(first|second|then|finally|step)\b',
    r'\b(solved|approach|strategy|analyzed|debugged|root cause)\b',
]
_METRIC_EVIDENCE = [
    r'\d+%|\d+ percent|\d+x\b|reduced by|improved by|increased by',
    r'\b\d+ (?:users|customers|requests|records|hours|days)\b',
]


def _score_turn(question, answer, relevance):
    """Score one turn's criteria 0-100 based ONLY on the actual answer text.

    Returns (criterion_scores, evidence_map, per_criterion_reasons).
    """
    word_count = len(_words(answer))
    unique_ratio = (len(set(_words(answer))) / word_count) if word_count else 0.0

    relevance_map = {
        RELEVANT: 1.0,
        PARTIALLY_RELEVANT: 0.45,
        IRRELEVANT: 0.0,
        NO_ANSWER: 0.0,
    }
    rel_factor = relevance_map[relevance['classification']]

    # --- content_relevance: dominated by whether the question was addressed
    if relevance['classification'] == NO_ANSWER:
        content = 0
    elif relevance['classification'] == IRRELEVANT:
        content = 0  # fluent but unrelated speech earns nothing
    else:
        content = round(55 * rel_factor + min(25, max(0, (word_count - 15)) * 1.2))
        if relevance['classification'] == PARTIALLY_RELEVANT:
            content = min(content, 45)
    content = int(min(100, max(0, content)))

    # --- communication: clarity/fluency of the ACTUAL speech
    if relevance['classification'] in (NO_ANSWER,):
        communication = 0
    elif relevance['classification'] == IRRELEVANT:
        # Speaking fluently about an unrelated topic shows delivery only.
        communication = min(40, word_count // 2)
    else:
        base = min(70, 30 + word_count)  # length shows elaboration
        clarity = int(unique_ratio * 30)  # varied vocabulary
        communication = min(100, base + clarity)

    # --- technical_depth: only from concrete technical content actually said
    tech_ev = _find_evidence(answer, _TECH_EVIDENCE)
    metric_ev = _find_evidence(answer, _METRIC_EVIDENCE)
    if relevance['classification'] in (NO_ANSWER, IRRELEVANT):
        technical = 0
    else:
        technical = 0
        if tech_ev:
            technical += 55
        if metric_ev:
            technical += 25
        # extra tech terms mentioned
        tech_terms = len(set(_words(answer)) & {
            'react', 'python', 'java', 'javascript', 'node', 'sql', 'database',
            'docker', 'aws', 'api', 'hooks', 'redux', 'rest', 'graphql',
            'component', 'service', 'backend', 'frontend', 'deploy', 'test',
        })
        technical += min(20, tech_terms * 7)
        technical = min(100, technical)

    # --- leadership: only when the transcript demonstrates it
    leadership = 0
    if relevance['classification'] in (RELEVANT, PARTIALLY_RELEVANT):
        lead_ev = _find_evidence(answer, _TEAM_EVIDENCE)
        if lead_ev:
            leadership = 65 if relevance['classification'] == RELEVANT else 40

    # --- listening: only when the transcript demonstrates it
    listening = 0
    if relevance['classification'] in (RELEVANT, PARTIALLY_RELEVANT):
        listen_ev = _find_evidence(answer, _LISTEN_EVIDENCE)
        if listen_ev:
            listening = 65 if relevance['classification'] == RELEVANT else 40

    # --- logical_reasoning: structure/cause-effect actually present
    reasoning = 0
    if relevance['classification'] in (RELEVANT, PARTIALLY_RELEVANT):
        reason_ev = _find_evidence(answer, _REASON_EVIDENCE)
        if reason_ev:
            reasoning = 60 if relevance['classification'] == RELEVANT else 35
        if metric_ev:
            reasoning = min(100, reasoning + 15)

    scores = {
        'content_relevance': content,
        'communication': communication,
        'technical_depth': technical,
        'leadership': leadership,
        'listening': listening,
        'logical_reasoning': reasoning,
    }

    evidence = {
        'content_relevance': relevance['reason'],
        'communication': (
            f'Candidate spoke {word_count} words '
            f'({int(unique_ratio * 100)}% unique vocabulary).'
            if word_count else 'No speech captured for this question.'
        ),
        'technical_depth': ' '.join(
            e for e in (tech_ev,
                        (f'Measurable outcome stated: {metric_ev}' if metric_ev else None))
            if e) or 'No specific technical work was described.',
        'leadership': _find_evidence(answer, _TEAM_EVIDENCE)
                      or 'No leadership behaviour was demonstrated in this answer.',
        'listening': _find_evidence(answer, _LISTEN_EVIDENCE)
                     or 'No listening/collaboration behaviour was demonstrated.',
        'logical_reasoning': reason_ev if (reason_ev := _find_evidence(answer, _REASON_EVIDENCE))
                             or True else '',
    }
    if not scores['logical_reasoning']:
        evidence['logical_reasoning'] = 'No structured reasoning was expressed in this answer.'
    elif not evidence['logical_reasoning']:
        evidence['logical_reasoning'] = 'Reasoning inferred from answer structure only.'

    return scores, evidence


# ---------------------------------------------------------------------------
# Overall evaluation
# ---------------------------------------------------------------------------

def evaluate_interview(transcript, questions=None):
    """Evaluate a full interview transcript with evidence-based scoring.

    transcript: list of {question, answer, transcript_status?}
    questions:  optional list of the session's questions (used when a turn
                lacks its own question text).

    Returns the result dict stored on the session and returned to the UI:
      score, feedback, strengths, mistakes, details, stats, evaluation_method
    """
    if questions is None:
        questions = []

    turns = []
    for i, item in enumerate(transcript or []):
        question = (item.get('question') if isinstance(item, dict) else None) \
            or (questions[i] if i < len(questions) else '')
        answer, status = resolve_transcript_entry(item)
        turns.append({'index': i, 'question': question, 'answer': answer,
                      'status': status})

    total = len(turns)
    criterion_totals = {k: 0.0 for k in EVALUATION_WEIGHTS}
    weighted_total = 0.0
    valid = 0
    low_conf = 0
    no_answer_count = 0
    irrelevant_count = 0
    partially_count = 0
    relevant_count = 0
    details = []

    for turn in turns:
        relevance = classify_relevance(turn['question'], turn['answer'])

        if turn['status'] == 'no_answer':
            relevance = {'classification': NO_ANSWER, 'overlap': 0,
                         'reason': 'No usable answer content was provided for this question.'}
            no_answer_count += 1
        elif turn['status'] == 'low_confidence':
            low_conf += 1
            # LOW_CONFIDENCE transcripts are never treated as strong evidence:
            # their relevance ceiling is partial credit, never full marks.
            cls = relevance['classification']
            if cls == RELEVANT:
                relevance = dict(relevance, classification=PARTIALLY_RELEVANT,
                                 reason=relevance['reason'] +
                                 ' (Low-confidence transcription - capped at partial credit.)')
            if relevance['classification'] == RELEVANT:
                relevant_count += 1
            elif relevance['classification'] == PARTIALLY_RELEVANT:
                partially_count += 1
            elif relevance['classification'] == IRRELEVANT:
                irrelevant_count += 1
            else:
                no_answer_count += 1
        elif relevance['classification'] == RELEVANT:
            relevant_count += 1
        elif relevance['classification'] == PARTIALLY_RELEVANT:
            partially_count += 1
        elif relevance['classification'] == IRRELEVANT:
            irrelevant_count += 1
        elif relevance['classification'] == NO_ANSWER:
            # Non-empty text that still carries no usable content
            # (e.g. a placeholder like "No answer provided").
            no_answer_count += 1

        scores, evidence = _score_turn(turn['question'], turn['answer'], relevance)
        if scores['content_relevance'] > 0:
            valid += 1

        turn_weighted = 0.0
        for key, weight in EVALUATION_WEIGHTS.items():
            criterion_totals[key] += scores[key]
            turn_weighted += scores[key] * (weight / 100.0)
        weighted_total += turn_weighted

        details.append({
            'question_number': turn['index'] + 1,
            'question': turn['question'],
            'answer': turn['answer'],
            'classification': relevance['classification'],
            'relevance_reason': relevance['reason'],
            'scores': scores,
            'weighted_contribution': round(turn_weighted, 2),
            'evidence': evidence,
            'transcript_status': turn['status'],
        })

    final_score = round(min(100.0, max(0.0, weighted_total / total)) if total else 0.0, 2)
    criterion_avg = {k: round(v / total, 1) if total else 0 for k, v in criterion_totals.items()}

    # Pass/Fail is derived ONLY from the final score against the fixed pass
    # mark. The evaluator never fabricates a pass: e.g. an interview whose
    # answers were all empty/irrelevant scores low and is recorded as FAIL.
    passed = bool(final_score >= PASS_MARK)

    # ---- Honest feedback derived from the ACTUAL counts -------------------
    breakdown = (
        f'{valid} of {total} answers substantively addressed their question '
        f'({relevant_count} fully relevant, {partially_count} partially, '
        f'{irrelevant_count} unrelated, {no_answer_count} missing).'
    )
    if valid == 0:
        if irrelevant_count and no_answer_count:
            cause = (f'{irrelevant_count} answer(s) discussed unrelated topics and '
                     f'{no_answer_count} had no usable content.')
        elif irrelevant_count:
            cause = (f'{irrelevant_count} answer(s) discussed topics unrelated '
                     'to their questions.')
        else:
            cause = f'{no_answer_count} answer(s) contained no usable content.'
        feedback = (
            f'No valid substantive answers were recorded across the {total} '
            f'question(s): {cause} The score reflects that none of the responses '
            'addressed their questions. Please complete the interview with '
            'answers related to each question.'
        )
        strengths = ['Completed the interview session end-to-end.']
        mistakes = [
            'Answers did not address the questions asked.',
            'No concrete examples or technical detail were provided.',
        ]
    else:
        feedback_parts = [breakdown]
        if low_conf:
            feedback_parts.append(
                f'{low_conf} answer(s) were transcribed with low confidence '
                'and were scored conservatively.'
            )
        if criterion_avg['technical_depth'] >= 55:
            feedback_parts.append(
                'You grounded answers in concrete technical work, which the '
                'evidence review confirms.'
            )
        if criterion_avg['leadership'] <= 20:
            feedback_parts.append(
                'Little leadership or team-coordination behaviour was evident '
                'in your answers.'
            )
        if criterion_avg['logical_reasoning'] <= 25:
            feedback_parts.append(
                'Answers rarely explained reasoning (cause/effect, structure).'
            )
        feedback = ' '.join(feedback_parts)

        strengths = []
        if criterion_avg['communication'] >= 50:
            strengths.append('Clear, fluent delivery in the answers given.')
        if criterion_avg['technical_depth'] >= 50:
            strengths.append('Concrete technical examples drawn from your stated experience.')
        if relevant_count:
            strengths.append(f'{relevant_count} answer(s) stayed on topic.')
        if not strengths:
            strengths.append('Engaged with the interview process.')

        mistakes = []
        if irrelevant_count:
            mistakes.append(f'{irrelevant_count} answer(s) did not address the question asked.')
        if no_answer_count:
            mistakes.append(f'{no_answer_count} question(s) had no usable answer.')
        if criterion_avg['logical_reasoning'] < 40:
            mistakes.append('Structure your answers (e.g. STAR: Situation, Task, Action, Result).')
        if criterion_avg['technical_depth'] < 40:
            mistakes.append('Include specific technologies, actions and measurable outcomes.')
        if not mistakes:
            mistakes.append('Keep grounding answers in specific evidence and outcomes.')

    return {
        'score': final_score,
        'passed': passed,
        'status': 'PASS' if passed else 'FAIL',
        'pass_mark': PASS_MARK,
        'feedback': feedback,
        'strengths': strengths,
        'mistakes': mistakes,
        'stats': {
            'total_questions': total,
            'valid_answers': valid,
            'relevant_answers': relevant_count,
            'partially_relevant_answers': partially_count,
            'irrelevant_answers': irrelevant_count,
            'no_answer_count': no_answer_count,
            'low_confidence_count': low_conf,
        },
        'criteria_averages': criterion_avg,
        'weights': dict(EVALUATION_WEIGHTS),
        'details': details,
        'evaluation_method': 'evidence_based',
        'evaluated_at': datetime.utcnow().isoformat() + 'Z',
    }
