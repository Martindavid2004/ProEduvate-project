# aptitude_routes.py

from flask import Blueprint, jsonify, request
from ..services.aptitude_service import (
    generate_aptitude_questions,
    generate_practice_questions,
    evaluate_aptitude_test,
    get_topic_concepts,
    get_topics_list,
    DEFAULT_TEST_QUESTIONS,
    MAX_TEST_QUESTIONS,
    _clamp_test_length,
)
from ..database import users_collection, submissions_collection
from ..services import assessment_state
from bson import ObjectId
from datetime import datetime

aptitude_bp = Blueprint('aptitude_bp', __name__, url_prefix='/api/aptitude')

@aptitude_bp.route('/topics', methods=['GET'])
def get_topics():
    """Get list of all aptitude topics"""
    try:
        topics = get_topics_list()
        return jsonify({
            'success': True,
            'topics': topics
        }), 200
    except Exception as e:
        print(f"Error fetching topics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch topics'
        }), 500

@aptitude_bp.route('/concepts/<topic>', methods=['GET'])
def get_concepts(topic):
    """Get learning concepts for a specific topic"""
    try:
        print(f"Fetching concepts for topic: '{topic}'")
        
        concepts = get_topic_concepts(topic)
        
        if not concepts:
            print(f"Failed to fetch concepts for topic: '{topic}'")
            return jsonify({
                'success': False,
                'message': f'Topic "{topic}" not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': concepts
        }), 200
    except Exception as e:
        print(f"Error fetching concepts: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to fetch concepts: {str(e)}'
        }), 500

@aptitude_bp.route('/practice/<topic>', methods=['GET'])
def get_practice(topic):
    """Get practice questions for a topic"""
    try:
        num_questions = int(request.args.get('count', 10))
        
        print(f"Generating practice questions for topic: '{topic}' (count: {num_questions})")
        
        practice_questions = generate_practice_questions(topic, num_questions)
        
        if not practice_questions:
            print(f"Failed to generate practice questions for topic: '{topic}'")
            return jsonify({
                'success': False,
                'message': f'Topic "{topic}" not found or failed to generate questions'
            }), 404
        
        return jsonify({
            'success': True,
            'data': practice_questions
        }), 200
    except Exception as e:
        print(f"Error generating practice questions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to generate practice questions: {str(e)}'
        }), 500

@aptitude_bp.route('/test/generate', methods=['POST'])
def generate_test():
    """Generate a new aptitude test"""
    try:
        data = request.get_json() or {}
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'medium')
        # REVERTED TO NORMAL LENGTH: the default (and the hard cap) is the
        # normal 10-15 question test. A client asking for 50 (old frontend)
        # is silently clamped to 15, so no caller can reintroduce the
        # oversized paper.
        num_questions = _clamp_test_length(data.get('num_questions', DEFAULT_TEST_QUESTIONS))
        
        print(f"Generating test for topic: '{topic}', difficulty: {difficulty}, questions: {num_questions}")
        
        if not topic:
            return jsonify({
                'success': False,
                'message': 'Topic is required'
            }), 400

        # Attempt lookup happens BEFORE question generation: an existing
        # attempt is resumed as-is (never re-generated) and a finished one is
        # locked, so a completed/failed/expired attempt can never trigger
        # another AI question generation or a new attempt (BUG 10/11).
        # RETAKE FLOW: the client may explicitly request a retake; the old
        # attempt is then archived (kept for history with its score) and a
        # brand-new attempt is created. Without retake=True a finished
        # attempt still returns 409 - but with canRetake=True so the UI can
        # offer a "Retake Assessment" button instead of a dead end.
        student_id = str(data.get('student_id') or '')
        retake = bool(data.get('retake'))
        attempt = None
        created = False
        attempt_key = f"{topic}_{student_id}" if student_id else None
        if attempt_key and not retake:
            attempt, _active = assessment_state.get_attempt_status(
                assessment_state.TYPE_APTITUDE, attempt_key)
            if attempt and attempt.get('status') != assessment_state.STATUS_IN_PROGRESS:
                # COMPLETED/FAILED attempts are locked - no restart, no regen.
                # The client is told a retake IS possible (canRetake) so it
                # can render the retake action.
                return jsonify({
                    'success': False,
                    'message': 'This assessment is already finished and cannot be restarted.',
                    'status': attempt.get('status'),
                    'failureReason': attempt.get('failure_reason'),
                    'attempt': assessment_state.serialize_attempt(attempt),
                    'canRetake': True,
                }), 409

        if attempt:
            # Resume: reuse the questions stored on the attempt so a refresh
            # shows the SAME question set (and the AI is not called again).
            question_list = attempt.get('questions') or []
            difficulty = (attempt.get('meta') or {}).get('difficulty', difficulty)
            if not question_list:
                # Legacy attempt created before questions were stored.
                questions = generate_aptitude_questions(topic, difficulty, num_questions)
                if not questions:
                    print(f"Failed to generate test questions for topic: '{topic}'")
                    return jsonify({
                        'success': False,
                        'message': f'Topic "{topic}" not found or failed to generate questions'
                    }), 404
                question_list = questions.get('questions', [])
                submissions_collection.update_one(
                    {'_id': attempt['_id']},
                    {'$set': {'questions': question_list}})
        else:
            questions = generate_aptitude_questions(topic, difficulty, num_questions)
            if not questions:
                print(f"Failed to generate test questions for topic: '{topic}'")
                return jsonify({
                    'success': False,
                    'message': f'Topic "{topic}" not found or failed to generate questions'
                }), 404
            question_list = questions.get('questions', [])

        if attempt_key:
            if attempt is None:
                # Fresh attempt: SERVER-side start/expiry timestamps are set
                # here; the generated questions are stored ON the attempt so
                # refreshes resume with the same set. retake=True archives a
                # previous finished attempt and starts a fresh one.
                attempt, created = assessment_state.start_assessment(
                    assessment_state.TYPE_APTITUDE,
                    attempt_key,
                    assessment_state.APTITUDE_DURATION_MINUTES,
                    total_questions=len(question_list),
                    meta={'topic': topic, 'difficulty': difficulty},
                    extra={
                        'topic': topic,
                        'student_id': student_id,
                        'test_id': None,
                        'questions': question_list,
                    },
                    retake=retake,
                )
            elif attempt.get('total_questions') != len(question_list):
                submissions_collection.update_one(
                    {'_id': attempt['_id']},
                    {'$set': {
                        'questions': question_list,
                        'total_questions': len(question_list),
                    }})

        test_id = str(attempt['_id'])

        print(f"Test generated successfully with {len(question_list)} questions")
        
        response = {
            'success': True,
            'test_id': test_id,
            'topic': topic,
            'difficulty': difficulty,
            'num_questions': num_questions if created else len(question_list),
            'duration_minutes': assessment_state.APTITUDE_DURATION_MINUTES,
            'questions': question_list,
            'created': created,
        }
        if student_id:
            response['attempt'] = assessment_state.serialize_attempt(attempt)
            response['serverTime'] = datetime.utcnow().isoformat()
        return jsonify(response), 200
    except Exception as e:
        print(f"Error generating test: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to generate test: {str(e)}'
        }), 500

@aptitude_bp.route('/test/fail', methods=['POST'])
def fail_test():
    """Automatic failure for a training-section test (TAB_SWITCH / TIME_EXPIRED).
    Server validates the attempt is still active before storing FAILED."""
    try:
        data = request.get_json() or {}
        test_id = data.get('test_id')
        reason = data.get('reason') or assessment_state.FAILURE_TAB_SWITCH
        if reason not in (assessment_state.FAILURE_TAB_SWITCH, assessment_state.FAILURE_TIME_EXPIRED):
            reason = assessment_state.FAILURE_TAB_SWITCH

        attempt = _find_aptitude_attempt(test_id, data)
        if not attempt:
            return jsonify({'success': False, 'message': 'Test attempt not found'}), 404

        doc, already_final = assessment_state.fail_assessment(attempt, reason)
        # Failed (tab-switch/expiry) attempts belong in the student's
        # progress history too, not only normal submissions (BUG 12).
        if not already_final:
            _sync_aptitude_progress(doc)
        return jsonify({
            'success': True,
            'alreadyFinal': already_final,
            'attempt': assessment_state.serialize_attempt(doc),
        }), 200
    except Exception as e:
        print(f"Error failing test: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to record test failure'}), 500

@aptitude_bp.route('/test/submit', methods=['POST'])
def submit_test():
    """Submit aptitude test answers for evaluation"""
    try:
        data = request.get_json()
        test_id = data.get('test_id')
        topic = data.get('topic')
        questions = data.get('questions')
        answers = data.get('answers')
        time_taken = data.get('time_taken', 0)
        
        if not all([test_id, topic, questions, answers]):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Locate the server-side attempt (new attempts are stored by _id;
        # fall back to the legacy in-memory test_id format).
        attempt = _find_aptitude_attempt(test_id, data)
        if attempt:
            if attempt.get('status') != assessment_state.STATUS_IN_PROGRESS:
                return jsonify({
                    'success': False,
                    'message': 'This assessment has already been submitted or failed.',
                    'status': attempt.get('status'),
                    'failureReason': attempt.get('failure_reason'),
                    'attempt': assessment_state.serialize_attempt(attempt),
                    'canRetake': True,
                }), 409

            doc, error = assessment_state.evaluate_and_store(
                attempt, questions, answers, time_taken=time_taken)
            if error:
                # Expired-at-deadline submissions land here with the attempt
                # now FAILED/TIME_EXPIRED - sync progress for them as well.
                if doc and doc.get('status') == assessment_state.STATUS_FAILED \
                        and doc.get('failure_reason') == assessment_state.FAILURE_TIME_EXPIRED:
                    _sync_aptitude_progress(doc)
                return jsonify({
                    'success': False,
                    'message': error.get('error', 'Submission rejected.'),
                    'status': error.get('status'),
                    'failureReason': doc.get('failure_reason') if doc else None,
                    'attempt': assessment_state.serialize_attempt(doc),
                    'canRetake': True,
                }), 409

            _sync_aptitude_progress(doc)

            return jsonify({
                'success': True,
                'evaluation': doc.get('evaluation'),
                'attempt': assessment_state.serialize_attempt(doc),
                'failed': doc.get('status') == assessment_state.STATUS_FAILED,
                'failureReason': doc.get('failure_reason'),
            }), 200

        # ---- Legacy fallback (attempt created before this change) ----
        student_id = data.get('student_id')

        # Evaluate the test
        evaluation = evaluate_aptitude_test(questions, answers)
        
        # Save submission to database
        submission = {
            'student_id': student_id,
            'test_id': test_id,
            'type': 'aptitude',
            'topic': topic,
            'total_questions': evaluation['total_questions'],
            'correct_answers': evaluation['correct_answers'],
            'incorrect_answers': evaluation['incorrect_answers'],
            'unanswered': evaluation['unanswered'],
            'score': evaluation['score'],
            'time_taken': time_taken,
            'submitted_at': datetime.utcnow(),
            'answers': answers,
            'evaluation': evaluation
        }
        
        submissions_collection.insert_one(submission)
        
        # Update student's aptitude progress
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {
                '$push': {
                    'aptitude_history': {
                        'topic': topic,
                        'score': evaluation['score'],
                        'date': datetime.utcnow()
                    }
                }
            }
        )
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        }), 200
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to submit test'
        }), 500

def _find_aptitude_attempt(test_id, data=None):
    """Locate an aptitude attempt document.

    New attempts are keyed by their MongoDB _id. Also accepts the legacy
    '<topic>_<student_id>' composite key format for compatibility.
    """
    data = data or {}
    if test_id and ObjectId.is_valid(test_id):
        doc = submissions_collection.find_one({
            '_id': ObjectId(test_id),
            'type': assessment_state.TYPE_APTITUDE,
        })
        if doc:
            return doc
    student_id = data.get('student_id')
    topic = data.get('topic')
    if student_id and topic:
        return submissions_collection.find_one({
            assessment_state._base_key_field(assessment_state.TYPE_APTITUDE):
                f"{topic}_{student_id}",
        })
    return None


def _sync_aptitude_progress(doc):
    """Push a finished aptitude attempt into the student's progress history."""
    try:
        student_id = doc.get('student_id')
        topic = doc.get('topic')
        if not student_id or not ObjectId.is_valid(student_id):
            return
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$push': {
                'aptitude_history': {
                    'topic': topic,
                    'score': doc.get('score', 0),
                    'status': doc.get('status'),
                    'failure_reason': doc.get('failure_reason'),
                    'date': datetime.utcnow(),
                }
            }}
        )
    except Exception as e:
        print(f"Warning: could not sync aptitude progress: {e}")


@aptitude_bp.route('/progress/<student_id>', methods=['GET'])
def get_progress(student_id):
    """Get student's aptitude progress"""
    try:
        # Get all finished aptitude submissions for the student
        # (in-progress attempts have no score/submitted_at yet and are excluded)
        submissions = [s for s in submissions_collection.find({
            'student_id': student_id,
            'type': 'aptitude',
            'score': {'$ne': None}
        }).sort('submitted_at', -1)]
        
        # Calculate overall statistics
        if submissions:
            total_tests = len(submissions)
            avg_score = sum(s['score'] for s in submissions) / total_tests
            best_score = max(s['score'] for s in submissions)
            
            # Topic-wise performance
            topic_performance = {}
            for sub in submissions:
                topic = sub['topic']
                if topic not in topic_performance:
                    topic_performance[topic] = []
                topic_performance[topic].append(sub['score'])
            
            topic_stats = {
                topic: {
                    'avg_score': sum(scores) / len(scores),
                    'attempts': len(scores),
                    'best_score': max(scores)
                }
                for topic, scores in topic_performance.items()
            }
            
            return jsonify({
                'success': True,
                'statistics': {
                    'total_tests': total_tests,
                    'average_score': round(avg_score, 2),
                    'best_score': round(best_score, 2),
                    'topic_performance': topic_stats
                },
                'recent_tests': [
                    {
                        'topic': s['topic'],
                        'score': s['score'],
                        'date': s['submitted_at'].isoformat(),
                        'time_taken': s.get('time_taken', 0)
                    }
                    for s in submissions[:10]
                ]
            }), 200
        else:
            return jsonify({
                'success': True,
                'statistics': {
                    'total_tests': 0,
                    'average_score': 0,
                    'best_score': 0,
                    'topic_performance': {}
                },
                'recent_tests': []
            }), 200
    except Exception as e:
        print(f"Error fetching progress: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch progress'
        }), 500


@aptitude_bp.route('/test/status', methods=['GET'])
def get_test_status():
    """Fetch the server-side attempt state for a topic+student.

    Used by the topic overview to decide the primary action: Start / Resume
    / Retake, and to show the last result. Never starts an attempt.
    """
    try:
        topic = request.args.get('topic', '')
        student_id = str(request.args.get('student_id') or '')
        if not topic or not student_id:
            return jsonify({'success': False, 'message': 'topic and student_id are required'}), 400

        attempt_key = f"{topic}_{student_id}"
        attempt, active = assessment_state.get_attempt_status(
            assessment_state.TYPE_APTITUDE, attempt_key)

        last_finished = assessment_state.get_latest_finished_attempt(
            assessment_state.TYPE_APTITUDE, attempt_key)

        return jsonify({
            'success': True,
            'status': attempt.get('status') if attempt else assessment_state.STATUS_NOT_STARTED,
            'active': active,
            'attempt': assessment_state.serialize_attempt(attempt),
            'lastResult': assessment_state.serialize_attempt(last_finished),
            # A retake is ALWAYS offered once an attempt is finished - the
            # permanent lockout is gone (the backend re-validates on start).
            'canRetake': bool(last_finished),
        }), 200
    except Exception as e:
        print(f"Error fetching test status: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch test status'}), 500
