# aptitude_routes.py

from flask import Blueprint, jsonify, request
from ..services.aptitude_service import (
    generate_aptitude_questions,
    generate_practice_questions,
    evaluate_aptitude_test,
    get_topic_concepts,
    get_topics_list
)
from ..database import users_collection, submissions_collection
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
        data = request.get_json()
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'medium')
        num_questions = data.get('num_questions', 50)
        
        print(f"Generating test for topic: '{topic}', difficulty: {difficulty}, questions: {num_questions}")
        
        if not topic:
            return jsonify({
                'success': False,
                'message': 'Topic is required'
            }), 400
        
        questions = generate_aptitude_questions(topic, difficulty, num_questions)
        
        if not questions:
            print(f"Failed to generate test questions for topic: '{topic}'")
            return jsonify({
                'success': False,
                'message': f'Topic "{topic}" not found or failed to generate questions'
            }), 404
        
        # Generate test ID
        test_id = str(ObjectId())
        
        print(f"Test generated successfully with {len(questions.get('questions', []))} questions")
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'topic': topic,
            'difficulty': difficulty,
            'num_questions': num_questions,
            'duration_minutes': 60,
            'questions': questions.get('questions', [])
        }), 200
    except Exception as e:
        print(f"Error generating test: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to generate test: {str(e)}'
        }), 500

@aptitude_bp.route('/test/submit', methods=['POST'])
def submit_test():
    """Submit aptitude test answers for evaluation"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        test_id = data.get('test_id')
        topic = data.get('topic')
        questions = data.get('questions')
        answers = data.get('answers')
        time_taken = data.get('time_taken', 0)
        
        if not all([student_id, test_id, topic, questions, answers]):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
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

@aptitude_bp.route('/progress/<student_id>', methods=['GET'])
def get_progress(student_id):
    """Get student's aptitude progress"""
    try:
        # Get all aptitude submissions for the student
        submissions = list(submissions_collection.find({
            'student_id': student_id,
            'type': 'aptitude'
        }).sort('submitted_at', -1))
        
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
