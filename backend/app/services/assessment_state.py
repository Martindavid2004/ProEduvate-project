# assessment_state.py
"""
Server-side assessment state engine.

Shared logic used by BOTH teacher-assigned MCQ quizzes and Training Section
(aptitude) MCQ tests. The backend is the single source of truth:

- Assessment start time / expiry time are SERVER timestamps stored in MongoDB.
- All validation (expiry, duplicate submission, restart) is done server-side.
- Each attempt has exactly one authoritative final result record.

Attempts are stored in the existing `submissions_collection` (type
'quiz_assessment' / 'aptitude') so all existing consumers keep working.
"""

from datetime import datetime, timedelta

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from ..database import submissions_collection

# Assessment types stored in submissions_collection
TYPE_TEACHER_QUIZ = 'quiz_assessment'      # teacher-assigned MCQ assessments
TYPE_APTITUDE = 'aptitude'                 # training-section MCQs (existing type)

# Canonical status values
STATUS_NOT_STARTED = 'NOT_STARTED'
STATUS_IN_PROGRESS = 'IN_PROGRESS'
STATUS_COMPLETED = 'COMPLETED'
STATUS_FAILED = 'FAILED'
STATUS_PASS = 'PASS'
STATUS_FAIL = 'FAIL'

FINAL_STATUSES = (STATUS_PASS, STATUS_FAIL, STATUS_FAILED, STATUS_COMPLETED)

# Failure reasons
FAILURE_TAB_SWITCH = 'TAB_SWITCH'
FAILURE_TIME_EXPIRED = 'TIME_EXPIRED'

# Minimum passing percentage (consistent with the existing 70% quiz feedback rule)
PASS_PERCENTAGE = 70.0

QUIZ_DURATION_MINUTES = 10       # teacher-assigned MCQ assessments
APTITUDE_DURATION_MINUTES = 60   # training-section tests (existing 60-minute rule)

FAILURE_MESSAGES = {
    FAILURE_TAB_SWITCH: 'Assessment failed because you switched to another browser tab or window.',
    FAILURE_TIME_EXPIRED: 'Assessment Failed - Time Expired.',
}


def ensure_attempt_indexes():
    """Create the unique index that makes attempt creation race-proof.

    Called once at app startup. Safe to call repeatedly (create_index is
    idempotent). With this index, two concurrent start requests can never
    create two attempts for the same assessment+student pair: one wins the
    insert, the loser re-reads the winner's document.

    Uses the pymongo-recommended [(field, ASCENDING)] list-of-tuples spec
    rather than the deprecated bare-string form to avoid DeprecationWarning
    in pymongo >= 4 and ensure forward compatibility.
    """
    for assessment_type in (TYPE_TEACHER_QUIZ, TYPE_APTITUDE):
        field = _base_key_field(assessment_type)
        submissions_collection.create_index(
            [(field, ASCENDING)],
            unique=True,
            partialFilterExpression={field: {'$type': 'string'}},
            name=f'uniq_{field}',
            background=True,
        )


def _utcnow():
    return datetime.utcnow()


def _iso(dt):
    """ISO-8601 with explicit UTC marker so the browser parses the timestamp
    with Date(...) in UTC. Naive isoformat() made the frontend interpret the
    server time as LOCAL time, skewing the countdown by the UTC offset."""
    if isinstance(dt, datetime):
        return dt.isoformat() + 'Z'
    return dt


def _base_key_field(assessment_type):
    """Every attempt carries a stable unique key field for idempotent lookup."""
    return f"{assessment_type}_key"


def remaining_seconds(attempt):
    """Seconds left based on the SERVER expiry timestamp."""
    if not attempt:
        return 0
    expires_at = attempt.get('assessment_expires_at')
    if not isinstance(expires_at, datetime):
        return 0
    return max(0, int((expires_at - _utcnow()).total_seconds()))


def serialize_attempt(attempt):
    """Convert a stored attempt document to a frontend-safe dict."""
    if not attempt:
        return None
    return {
        'id': str(attempt.get('_id', '')),
        'status': attempt.get('status'),
        'failureReason': attempt.get('failure_reason'),
        'startedAt': _iso(attempt.get('assessment_started_at')),
        'expiresAt': _iso(attempt.get('assessment_expires_at')),
        'remainingSeconds': remaining_seconds(attempt),
        'durationMinutes': attempt.get('duration_minutes'),
        'score': attempt.get('score'),
        'passed': attempt.get('passed'),
        'submittedAt': _iso(attempt.get('submitted_at')),
        'evaluation': attempt.get('evaluation'),
    }


def _find_attempt(assessment_type, attempt_key):
    return submissions_collection.find_one({_base_key_field(assessment_type): attempt_key})


def get_attempt_status(assessment_type, attempt_key):
    """
    Return (attempt_doc, is_active). An expired IN_PROGRESS attempt is
    automatically finalized as FAILED / TIME_EXPIRED (server is the authority).
    """
    attempt = _find_attempt(assessment_type, attempt_key)
    if not attempt:
        return None, False

    if attempt.get('status') == STATUS_IN_PROGRESS:
        expires_at = attempt.get('assessment_expires_at')
        if isinstance(expires_at, datetime) and _utcnow() >= expires_at:
            attempt = finalize_failure(
                attempt,
                FAILURE_TIME_EXPIRED,
                total_questions=attempt.get('total_questions', 0),
            )
    return attempt, attempt.get('status') == STATUS_IN_PROGRESS


def is_final(status):
    """True when the status is terminal (completed / failed / pass / fail)."""
    return status in FINAL_STATUSES


def archive_attempt(attempt):
    """Retire a FINISHED attempt so the student can start a fresh one (retake).

    The attempt record is never deleted - history, scores and the teacher
    view keep working. Its unique attempt-key field is $unset (freeing the
    sparse partial-index slot) and the key value is preserved on
    'retired_attempt_key', with the doc flagged 'retired'. The caller can
    then create a brand-new IN_PROGRESS attempt with the same key without
    violating the unique index.

    Returns True when a document was actually archived.
    """
    if not attempt or not is_final(attempt.get('status')):
        return False
    key_field = _base_key_field(attempt.get('type', TYPE_APTITUDE))
    key_value = attempt.get(key_field)
    if not key_value:
        # Already archived (defensive): nothing to free.
        return False
    res = submissions_collection.find_one_and_update(
        {
            '_id': attempt['_id'],
            key_field: key_value,
            # Never archive an attempt that went back IN_PROGRESS.
            'status': {'$in': list(FINAL_STATUSES)},
        },
        {
            '$set': {
                'retired': True,
                'retired_at': _utcnow(),
                'retired_attempt_key': key_value,
            },
            '$unset': {key_field: ''},
        },
    )
    return res is not None


def ensure_attempt_questions(attempt, fallback_questions):
    """Return the AUTHORITATIVE question list for an attempt.

    Attempts created after the dynamic-pooling feature store a per-attempt
    snapshot ('questions') captured at start time; every NEW attempt (and
    every retake) gets its own freshly shuffled selection, so a retake never
    replays the exact paper of a previous attempt.

    Legacy attempts without a snapshot fall back to the live assignment
    question list - in ORIGINAL order, because an in-flight student's saved
    answers map to that order by index (reordering mid-attempt would corrupt
    evaluation). The fallback is backfilled onto the attempt so the rest of
    the lifecycle (status/submit) sees one consistent list.
    """
    if not attempt:
        return list(fallback_questions or [])
    stored = attempt.get('questions')
    if isinstance(stored, list) and stored:
        return stored
    fallback = list(fallback_questions or [])
    if attempt.get('status') == STATUS_IN_PROGRESS and fallback:
        try:
            submissions_collection.update_one(
                {'_id': attempt['_id'], 'status': STATUS_IN_PROGRESS},
                {'$set': {'questions': fallback}},
            )
        except Exception:
            # Backfill is best-effort; evaluation still uses the fallback.
            pass
    return fallback


def start_assessment(assessment_type, attempt_key, duration_minutes,
                     total_questions, meta=None, extra=None, retake=False,
                     questions=None):
    """
    Start (or resume) a timed assessment attempt.

    - No attempt yet  -> create one with SERVER-side start/expiry timestamps.
    - Attempt exists  -> returned untouched (refresh/reopen can never reset
      the timer or duplicate the attempt).
    - Finished attempt-> returned locked; caller must not allow answering,
      UNLESS retake=True: the finished attempt is archived (kept for history
      with its score) and a brand-new attempt is created.

    `questions` (optional) is the per-attempt question snapshot. The caller
    shuffles/selects it BEFORE calling, so each attempt - including every
    retake - serves its own randomized paper (dynamic question pooling).
    The snapshot is stored on the attempt and is what /status and /submit
    use, keeping selection, display and evaluation consistent even if the
    teacher edits the assignment mid-attempt.

    Creation is race-proof: the unique attempt-key index means a concurrent
    double-start (double click / two tabs) can never insert two attempts. The
    loser of the insert re-reads the winner's document, so exactly ONE attempt
    exists per (assessment_type, attempt_key).

    Returns (attempt_doc, created: bool).
    """
    existing, _active = get_attempt_status(assessment_type, attempt_key)
    if existing:
        if retake and is_final(existing.get('status')):
            # Retake: release the unique key by archiving the old attempt,
            # then fall through and create a fresh one. If a concurrent
            # request archived it first, archive_attempt returns False and
            # we simply proceed - the key is free either way.
            archive_attempt(existing)
            existing = None
        else:
            return existing, False

    started_at = _utcnow()
    expires_at = started_at + timedelta(minutes=duration_minutes)
    doc = {
        _base_key_field(assessment_type): attempt_key,
        'type': assessment_type,
        'status': STATUS_IN_PROGRESS,
        'assessment_started_at': started_at,
        'assessment_expires_at': expires_at,
        'duration_minutes': duration_minutes,
        'total_questions': total_questions,
        'meta': meta or {},
        'answers': {},
        # Per-attempt question snapshot (dynamic pooling). None for attempts
        # whose caller did not supply one (legacy path).
        'questions': list(questions) if questions is not None else None,
        'submitted_at': None,
        'score': None,
        'passed': None,
        'failure_reason': None,
        'evaluation': None,
    }
    # Compatibility fields merged top-level so existing consumers
    # (teacher submissions view, progress endpoints) keep working.
    if extra:
        doc.update(extra)

    try:
        result = submissions_collection.insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc, True
    except DuplicateKeyError:
        # A concurrent start created the attempt first (BUG 5/6/9): reuse it.
        # Never overwrite the winner's start/expiry timestamps.
        existing, _active = get_attempt_status(assessment_type, attempt_key)
        if existing:
            return existing, False
        raise


def get_latest_finished_attempt(assessment_type, attempt_key):
    """Most recent FINISHED attempt for a key (retakes archive old docs and
    free the key, so finished attempts are looked up by retired_attempt_key
    OR the live key), newest first."""
    key_field = _base_key_field(assessment_type)
    doc = submissions_collection.find_one(
        {key_field: attempt_key, 'status': {'$in': list(FINAL_STATUSES)}},
        sort=[('submitted_at', -1)])
    if doc:
        return doc
    return submissions_collection.find_one(
        {'retired_attempt_key': attempt_key,
         'status': {'$in': list(FINAL_STATUSES)}},
        sort=[('submitted_at', -1)])


def finalize_failure(attempt, reason, total_questions=0):
    """
    Atomically lock an IN_PROGRESS attempt as FAILED with the given reason.
    The status guard makes concurrent tabs / duplicate calls harmless: the
    first finalization wins and is never overwritten.
    """
    now = _utcnow()
    res = submissions_collection.find_one_and_update(
        {
            '_id': attempt['_id'],
            'status': STATUS_IN_PROGRESS,
        },
        {
            '$set': {
                'status': STATUS_FAILED,
                'failure_reason': reason,
                'submitted_at': now,
                'passed': False,
                'score': 0,
                'evaluation': {
                    'total_questions': total_questions,
                    'correct_answers': 0,
                    'incorrect_answers': 0,
                    'unanswered': total_questions,
                    'score': 0,
                    'passed': False,
                    'performance': {
                        'level': 'Failed',
                        'message': FAILURE_MESSAGES.get(reason, 'Assessment failed.'),
                        'recommendation': 'Contact your instructor if you believe this was a mistake.',
                    },
                },
            }
        },
        return_document=True,
    )
    return res if res else submissions_collection.find_one({'_id': attempt['_id']})


def fail_assessment(attempt, reason):
    """Mark an active attempt FAILED (tab switch / expiry). Returns (doc, already_final)."""
    if not attempt or attempt.get('status') != STATUS_IN_PROGRESS:
        return attempt, True
    doc = finalize_failure(attempt, reason, total_questions=attempt.get('total_questions', 0))
    return doc, False


def normalize_answers(answers):
    """Convert frontend answer maps/lists into a stable {index: answer} dict."""
    normalized = {}
    if isinstance(answers, dict):
        for k, v in answers.items():
            try:
                normalized[str(int(k))] = v
            except (TypeError, ValueError):
                normalized[str(k)] = v
    elif isinstance(answers, list):
        for i, v in enumerate(answers):
            normalized[str(i)] = v
    return normalized


def _q_text(question):
    if isinstance(question, dict):
        return question.get('question')
    return question


def _q_field(question, key):
    if isinstance(question, dict):
        return question.get(key)
    return None


def evaluate_and_store(attempt, questions, answers, time_taken=None):
    """
    Evaluate answers, compute score / PASS-FAIL and store the authoritative
    final result on the attempt (single record, atomic status transition).

    Returns (attempt_doc, error) where error is a dict when the submission is
    rejected (not active / already submitted). A submission received after
    server expiry is recorded but marked FAILED / TIME_EXPIRED - it is never
    accepted as a normal submission.
    """
    if not attempt or attempt.get('status') != STATUS_IN_PROGRESS:
        return attempt, {
            'error': 'Assessment is not active.',
            'status': attempt.get('status') if attempt else None,
            'failureReason': attempt.get('failure_reason') if attempt else None,
        }

    expires_at = attempt.get('assessment_expires_at')
    now = _utcnow()
    expired = isinstance(expires_at, datetime) and now >= expires_at

    # Validate answers up front: never let a bad payload cause a 500 *after*
    # the attempt has already been finalized.
    if not isinstance(questions, (list, tuple)) or not questions:
        return attempt, {
            'error': 'No questions available for evaluation.',
            'status': STATUS_IN_PROGRESS,
        }

    normalized = normalize_answers(answers)

    total_questions = len(questions) if questions else attempt.get('total_questions', 0)
    correct = 0
    incorrect = 0
    unanswered = 0
    results = []
    for i, question in enumerate(questions or []):
        user_answer = normalized.get(str(i))
        correct_answer = _q_field(question, 'correct_answer')
        if user_answer is None or (isinstance(user_answer, str) and not user_answer.strip()):
            unanswered += 1
            status = 'unanswered'
        elif correct_answer is not None and \
                str(user_answer).strip().lower() == str(correct_answer).strip().lower():
            correct += 1
            status = 'correct'
        else:
            incorrect += 1
            status = 'incorrect'
        results.append({
            'question_number': i + 1,
            'question': _q_text(question),
            'options': _q_field(question, 'options'),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'explanation': _q_field(question, 'explanation'),
            # Category tag (Grammar / General Knowledge / Technical /
            # Logical Reasoning) surfaces in the answer-review UI.
            'category': _q_field(question, 'category'),
            'status': status,
        })

    score = round((correct / total_questions) * 100, 2) if total_questions else 0
    passed = score >= PASS_PERCENTAGE

    evaluation = {
        'total_questions': total_questions,
        'correct_answers': correct,
        'incorrect_answers': incorrect,
        'unanswered': unanswered,
        'score': score,
        'percentage': score,
        'passed': passed,
        'results': results,
        'performance': get_pass_fail_analysis(score, passed),
    }

    update = {
        # Expired submissions are FAILED in the SAME atomic update as normal
        # ones - there is no window where a late submission can ever be stored
        # as PASS/FAIL first (the old two-step flip raced with concurrent
        # finalizers like the tab-switch handler).
        'status': STATUS_FAILED if expired else (STATUS_PASS if passed else STATUS_FAIL),
        'passed': False if expired else passed,
        # A FAILED attempt always stores score 0 (same contract as
        # finalize_failure) so progress averages / teacher views never see a
        # nonzero score on a rejected submission. The computed breakdown is
        # still kept inside evaluation for transparency.
        'score': 0 if expired else score,
        'quiz_score': 0 if expired else score,
        'submitted_at': now,
        'failure_reason': FAILURE_TIME_EXPIRED if expired else None,
        'answers': normalized,
        'evaluation': dict(evaluation, passed=False,
                           performance=get_pass_fail_analysis(score, False, expired=True))
        if expired else evaluation,
    }
    if time_taken is not None:
        update['time_taken'] = time_taken

    res = submissions_collection.find_one_and_update(
        {'_id': attempt['_id'], 'status': STATUS_IN_PROGRESS},
        {'$set': update},
        return_document=True,
    )
    if not res:
        # Another request already finalized this attempt -> duplicate submission.
        return submissions_collection.find_one({'_id': attempt['_id']}), \
            {'error': 'Assessment has already been submitted.', 'status': attempt.get('status')}

    if expired:
        # Late submission: recorded, but NOT accepted as a normal submission.
        # e.g. expires 10:30:00, request arrives 10:30:05 -> FAILED/TIME_EXPIRED.
        return res, {
            'error': 'Assessment expired before the submission was received.',
            'status': STATUS_FAILED,
            'failureReason': FAILURE_TIME_EXPIRED,
            'expired': True,
        }

    return res, None


def get_pass_fail_analysis(score, passed, expired=False):
    if expired:
        return {
            'level': 'Failed',
            'message': f'Submission received after the deadline. Score {score}% was not accepted.',
            'recommendation': 'Contact your instructor if you believe this was a mistake.',
        }
    if passed:
        return {
            'level': 'Passed',
            'message': f'You passed with a score of {score}%.',
            'recommendation': 'Great work! Keep practicing to strengthen weak areas.',
        }
    return {
        'level': 'Failed',
        'message': f'You scored {score}% and did not reach the {PASS_PERCENTAGE:.0f}% pass mark.',
        'recommendation': 'Review the concepts and practice before your next attempt.',
    }
