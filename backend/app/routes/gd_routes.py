# gd_routes.py - Group Discussion Routes

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from ..database import gd_rounds_collection, gd_results_collection, users_collection, gd_notifications_collection
from bson import ObjectId
import random

gd_bp = Blueprint('gd_bp', __name__, url_prefix='/api/gd')

# Default GD topics
DEFAULT_GD_TOPICS = [
    "Impact of Artificial Intelligence on Employment",
    "Remote Work vs Office Work: Future of Workplace",
    "Social Media: Boon or Bane",
    "Climate Change and Corporate Responsibility",
    "Education System Reform in the Digital Age",
    "Work-Life Balance in Tech Industry",
    "Startup Culture vs Corporate Culture",
    "Impact of E-commerce on Traditional Retail",
    "Data Privacy in the Age of Big Tech",
    "Role of Youth in Nation Building",
    "Renewable Energy: Path to Sustainability",
    "Impact of Globalization on Local Businesses",
    "Mental Health Awareness in Workplace",
    "Gender Equality in Tech Industry",
    "Is Traditional Education Still Relevant?"
]

# Evaluation Criteria with default weights
DEFAULT_EVALUATION_CRITERIA = {
    "communication_skills": {"weight": 25, "description": "Clarity, articulation, and language proficiency"},
    "leadership": {"weight": 20, "description": "Initiative taking and group steering ability"},
    "logical_reasoning": {"weight": 20, "description": "Quality of arguments and critical thinking"},
    "content_relevance": {"weight": 20, "description": "Knowledge and relevance of points made"},
    "listening_team_dynamics": {"weight": 15, "description": "Active listening and team collaboration"}
}

@gd_bp.route('/topics', methods=['GET'])
def get_gd_topics():
    """Get list of available GD topics"""
    try:
        # In production, fetch from database
        return jsonify({
            "topics": DEFAULT_GD_TOPICS,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/evaluation-criteria', methods=['GET'])
def get_evaluation_criteria():
    """Get evaluation criteria with weights"""
    try:
        return jsonify({
            "criteria": DEFAULT_EVALUATION_CRITERIA,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/schedule', methods=['POST'])
def schedule_gd_round():
    """Admin/Teacher schedules a GD round"""
    try:
        data = request.get_json()
        
        gd_round = {
            "title": data.get("title", "Group Discussion Round"),
            "scheduled_time": data.get("scheduled_time"),
            "duration": data.get("duration", 20),  # minutes
            "topic": data.get("topic"),
            "allow_topic_selection": data.get("allow_topic_selection", False),
            "available_topics": data.get("available_topics", DEFAULT_GD_TOPICS),
            "num_ai_agents": data.get("num_ai_agents", 7),
            "ai_agent_voices": data.get("ai_agent_voices", []),  # List of male/female
            "assigned_students": data.get("assigned_students", []),
            "evaluation_criteria": data.get("evaluation_criteria", DEFAULT_EVALUATION_CRITERIA),
            "created_by": data.get("created_by"),
            "created_at": datetime.utcnow().isoformat(),
            "status": "scheduled"
        }
        
        result = gd_rounds_collection.insert_one(gd_round)
        gd_round['_id'] = str(result.inserted_id)
        
        # Create notifications for assigned students
        for student_id in gd_round['assigned_students']:
            notification = {
                "student_id": student_id,
                "gd_round_id": str(result.inserted_id),
                "title": f"GD Round Scheduled: {gd_round['title']}",
                "message": f"You have been assigned to a Group Discussion round scheduled for {gd_round['scheduled_time']}",
                "type": "gd_scheduled",
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            gd_notifications_collection.insert_one(notification)
        
        return jsonify({
            "message": "GD Round scheduled successfully",
            "gd_round": gd_round,
            "success": True
        }), 201
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/rounds', methods=['GET'])
def get_gd_rounds():
    """Get all GD rounds"""
    try:
        rounds = list(gd_rounds_collection.find())
        for round in rounds:
            round['_id'] = str(round['_id'])
        
        return jsonify({
            "rounds": rounds,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/student/<student_id>/rounds', methods=['GET'])
def get_student_gd_rounds(student_id):
    """Get GD rounds assigned to a specific student"""
    try:
        rounds = list(gd_rounds_collection.find({
            "assigned_students": student_id
        }))
        
        for round in rounds:
            round['_id'] = str(round['_id'])
        
        return jsonify({
            "rounds": rounds,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/notifications/<student_id>', methods=['GET'])
def get_student_notifications(student_id):
    """Get GD notifications for a student"""
    try:
        notifications = list(gd_notifications_collection.find({
            "student_id": student_id
        }).sort("created_at", -1))
        
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
        
        return jsonify({
            "notifications": notifications,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/notifications/<notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        gd_notifications_collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True}}
        )
        
        return jsonify({
            "message": "Notification marked as read",
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/round/<round_id>', methods=['GET'])
def get_gd_round_details(round_id):
    """Get details of a specific GD round"""
    try:
        round = gd_rounds_collection.find_one({"_id": ObjectId(round_id)})
        
        if not round:
            return jsonify({"error": "GD round not found", "success": False}), 404
        
        round['_id'] = str(round['_id'])
        
        return jsonify({
            "round": round,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/round/<round_id>/select-topic', methods=['POST'])
def select_topic(round_id):
    """Student selects a topic from available options"""
    try:
        data = request.get_json()
        selected_topic = data.get("topic")
        student_id = data.get("student_id")
        
        # Update the round with selected topic
        gd_rounds_collection.update_one(
            {"_id": ObjectId(round_id)},
            {"$set": {"topic": selected_topic, "topic_selected_by": student_id}}
        )
        
        return jsonify({
            "message": "Topic selected successfully",
            "topic": selected_topic,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/round/<round_id>/start', methods=['POST'])
def start_gd_round(round_id):
    """Start a GD round"""
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        
        # Update round status
        gd_rounds_collection.update_one(
            {"_id": ObjectId(round_id)},
            {"$set": {
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat(),
                "current_participant": student_id
            }}
        )
        
        # Get round details
        round = gd_rounds_collection.find_one({"_id": ObjectId(round_id)})
        
        return jsonify({
            "message": "GD round started",
            "round": {
                "_id": str(round['_id']),
                "topic": round['topic'],
                "duration": round['duration'],
                "num_ai_agents": round['num_ai_agents']
            },
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/round/<round_id>/submit-response', methods=['POST'])
def submit_response(round_id):
    """Submit a user's response during GD"""
    try:
        data = request.get_json()
        
        response_data = {
            "round_id": round_id,
            "student_id": data.get("student_id"),
            "response_text": data.get("response_text"),
            "timestamp": datetime.utcnow().isoformat(),
            "duration": data.get("duration", 0)  # How long they spoke
        }
        
        # Store response (you might want a separate collection)
        gd_rounds_collection.update_one(
            {"_id": ObjectId(round_id)},
            {"$push": {"responses": response_data}}
        )
        
        return jsonify({
            "message": "Response submitted",
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/round/<round_id>/evaluate', methods=['POST'])
def evaluate_gd_round(round_id):
    """Evaluate and complete a GD round"""
    try:
        data = request.get_json()
        
        # In a real implementation, this would use AI to analyze the responses
        # For now, we'll use mock evaluation
        
        responses = data.get("responses", [])
        evaluation_criteria = data.get("evaluation_criteria", DEFAULT_EVALUATION_CRITERIA)
        
        # Mock evaluation scores
        participants = []
        student_id = data.get("student_id")
        num_ai_agents = data.get("num_ai_agents", 7)
        
        # Evaluate student
        student_score = evaluate_participant(responses, evaluation_criteria, is_student=True)
        participants.append({
            "id": student_id,
            "name": "You",
            "type": "student",
            "scores": student_score["scores"],
            "total_score": student_score["total_score"],
            "rank": 0  # Will be determined after sorting
        })
        
        # Generate AI agent scores
        for i in range(num_ai_agents):
            ai_score = generate_ai_agent_score(evaluation_criteria)
            participants.append({
                "id": f"ai_agent_{i+1}",
                "name": f"AI Agent {i+1}",
                "type": "ai",
                "scores": ai_score["scores"],
                "total_score": ai_score["total_score"],
                "rank": 0
            })
        
        # Sort by total score and assign ranks
        participants.sort(key=lambda x: x["total_score"], reverse=True)
        for idx, participant in enumerate(participants):
            participant["rank"] = idx + 1
        
        # Get top 3
        top_3 = participants[:3]
        
        # Save results
        result = {
            "round_id": round_id,
            "student_id": student_id,
            "all_participants": participants,
            "top_3": top_3,
            "student_rank": next(p["rank"] for p in participants if p["type"] == "student"),
            "evaluation_criteria": evaluation_criteria,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        gd_results_collection.insert_one(result)
        
        # Update round status
        gd_rounds_collection.update_one(
            {"_id": ObjectId(round_id)},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }}
        )
        
        result['_id'] = str(result['_id'])
        
        return jsonify({
            "message": "GD round evaluated successfully",
            "results": result,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@gd_bp.route('/results/<student_id>', methods=['GET'])
def get_student_results(student_id):
    """Get all GD results for a student"""
    try:
        results = list(gd_results_collection.find({
            "student_id": student_id
        }).sort("completed_at", -1))
        
        for result in results:
            result['_id'] = str(result['_id'])
        
        return jsonify({
            "results": results,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

def evaluate_participant(responses, criteria, is_student=False):
    """Evaluate a participant based on their responses"""
    scores = {}
    
    for criterion_key, criterion_data in criteria.items():
        # In real implementation, use AI/NLP to evaluate
        # For now, generate realistic scores
        if is_student:
            # Give student slightly higher scores
            base_score = random.randint(70, 95)
        else:
            base_score = random.randint(60, 90)
        
        scores[criterion_key] = {
            "score": base_score,
            "weight": criterion_data["weight"]
        }
    
    # Calculate weighted total
    total_score = sum(
        (scores[k]["score"] * scores[k]["weight"]) / 100 
        for k in scores
    )
    
    return {
        "scores": scores,
        "total_score": round(total_score, 2)
    }

def generate_ai_agent_score(criteria):
    """Generate scores for AI agents"""
    scores = {}
    
    for criterion_key, criterion_data in criteria.items():
        base_score = random.randint(60, 95)
        scores[criterion_key] = {
            "score": base_score,
            "weight": criterion_data["weight"]
        }
    
    total_score = sum(
        (scores[k]["score"] * scores[k]["weight"]) / 100 
        for k in scores
    )
    
    return {
        "scores": scores,
        "total_score": round(total_score, 2)
    }

@gd_bp.route('/admin/config', methods=['GET', 'POST'])
def gd_admin_config():
    """Get or update GD configuration"""
    if request.method == 'GET':
        # Return current configuration
        return jsonify({
            "default_topics": DEFAULT_GD_TOPICS,
            "evaluation_criteria": DEFAULT_EVALUATION_CRITERIA,
            "default_duration": 20,
            "min_ai_agents": 5,
            "max_ai_agents": 10,
            "success": True
        }), 200
    else:
        # Update configuration
        try:
            data = request.get_json()
            # In production, save to database
            return jsonify({
                "message": "Configuration updated successfully",
                "success": True
            }), 200
        except Exception as e:
            return jsonify({"error": str(e), "success": False}), 500
