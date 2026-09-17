# gd_routes.py - Group Discussion Routes

import logging
import os
import tempfile

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..database import gd_rounds_collection, gd_results_collection, users_collection, gd_notifications_collection
from bson import ObjectId
from bson.errors import InvalidId
from .auth_routes import verify_jwt_token
from ..services.gd_service import GDService
from ..services.stt_service import (
    stt_service,
    AudioValidationError,
    ModelUnavailableError,
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    TRANSCRIPT_VALID,
    TRANSCRIPT_LOW_CONF,
    TRANSCRIPT_INVALID,
    TRANSCRIPT_NO_SPEECH,
)
import random

logger = logging.getLogger("stt")

gd_bp = Blueprint('gd_bp', __name__, url_prefix='/api/gd')

gd_service = GDService()

MIN_AI_AGENTS = 5
MAX_AI_AGENTS = 10
MAX_RESPONSE_LENGTH = 2000

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

def error_response(message, status_code=400):
    return jsonify({"error": message, "success": False, "text": ""}), status_code

def get_authenticated_user():
    """Verify JWT token from Authorization header and return user dict or error tuple.

    Failure-safe: a transient MongoDB outage (e.g. pymongo.errors.NetworkTimeout
    seen in the backend logs) must NEVER bubble out of this helper as an
    unhandled raw-HTML 500. When the DB is unreachable we degrade gracefully to
    the JWT claims themselves, which carry user_id/email/role.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, error_response("Unauthorized: Missing or invalid token", 401)

    token = auth_header.split(' ', 1)[1]
    payload = verify_jwt_token(token)
    if not payload:
        return None, error_response("Unauthorized: Invalid or expired token", 401)

    user_id = payload.get('user_id')
    user = None
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        # Invalid ObjectId or DB failure - try the email lookup, also guarded.
        try:
            user = users_collection.find_one({"email": payload.get('email')})
        except Exception as db_err:
            logging.warning("User DB lookup unavailable (%s) - using JWT claims", type(db_err).__name__)
            user = None

    if not user:
        user = {
            "_id": user_id,
            "email": payload.get('email'),
            "role": payload.get('role', 'student'),
            "name": payload.get('email', 'User')
        }
    return user, None

def validate_object_id(oid_str, param_name="round ID"):
    try:
        return ObjectId(oid_str), None
    except (InvalidId, TypeError, ValueError):
        return None, error_response(f"Invalid GD {param_name}", 400)

@gd_bp.route('/topics', methods=['GET'])
def get_gd_topics():
    """Get list of available GD topics"""
    user, err = get_authenticated_user()
    if err:
        return err
    try:
        return jsonify({
            "topics": DEFAULT_GD_TOPICS,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/evaluation-criteria', methods=['GET'])
def get_evaluation_criteria():
    """Get evaluation criteria with weights"""
    user, err = get_authenticated_user()
    if err:
        return err
    try:
        return jsonify({
            "criteria": DEFAULT_EVALUATION_CRITERIA,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using faster-whisper (offline speech-to-text fallback).

    Error contract (JSON body always; never a raw HTML traceback):
      400 - invalid audio request (missing/empty file, bad extension, too large)
      401 - missing/invalid auth token
      422 - audio could not be decoded / contains no usable audio
      503 - Whisper model unavailable (e.g. faster-whisper missing, model load failed)
      500 - unexpected transcription failure (details only in backend logs)
    """
    import time
    t_request = time.time()
    logger.info("[STT] Request received")

    user, err = get_authenticated_user()
    if err:
        return err

    tmp_path = None
    try:
        if 'audio' not in request.files:
            return error_response("No audio file provided", 400)

        audio_file = request.files['audio']
        if not audio_file or audio_file.filename == '':
            return error_response("No audio file selected", 400)

        # Validate size BEFORE writing to disk (do not trust client MIME type:
        # we only use the filename extension as a hint, and sanitize it).
        audio_file.stream.seek(0, os.SEEK_END)
        upload_size = audio_file.stream.tell()
        audio_file.stream.seek(0)
        if upload_size == 0:
            return error_response("Audio file is empty", 400)
        if upload_size > MAX_UPLOAD_BYTES:
            return error_response(
                f"Audio file too large ({upload_size // (1024 * 1024)} MB). Limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                413,
            )

        from werkzeug.utils import secure_filename

        # Sanitize the client-supplied filename: only its extension is used as
        # a hint, stored under a generated temp name -> no path traversal.
        safe_name = secure_filename(audio_file.filename) or 'recording.webm'
        ext = os.path.splitext(safe_name)[1].lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            ext = '.webm'

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        logger.info("[STT] Audio size: %d bytes | MIME type: %s | temp file created", upload_size, audio_file.mimetype)
        try:
            with os.fdopen(tmp_fd, 'wb') as f:
                audio_file.save(f)
        except Exception:
            if os.path.exists(tmp_path):
                audio_file.save(tmp_path)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return error_response("Audio file is empty", 400)

        # Transcribe using the cached faster-whisper model singleton.
        # stt_service.transcribe() now returns (text, meta) where meta includes:
        #   - status: VALID / LOW_CONFIDENCE / INVALID / NO_SPEECH
        #   - validation_reason: human-readable reason
        #   - quality: {avg_logprob, max_no_speech_prob, max_compression_ratio, segment_count}
        text, meta = stt_service.transcribe(tmp_path)

        stt_status = meta.get("status", TRANSCRIPT_NO_SPEECH if not text else TRANSCRIPT_VALID)
        validation_reason = meta.get("validation_reason", "")
        quality = meta.get("quality") or {}

        # INVALID/NO_SPEECH: do not send transcript to AI, return actionable user message
        if stt_status in (TRANSCRIPT_INVALID, TRANSCRIPT_NO_SPEECH) or not text:
            # Attempt loudness probe for a more specific user message
            loudness = None
            try:
                loudness = gd_service.get_audio_loudness(tmp_path)
            except Exception:
                pass

            if loudness is not None:
                mean_db, max_db = loudness
                logger.info("[STT] empty/invalid transcript; audio loudness mean=%.1fdB max=%.1fdB", mean_db, max_db)
                if max_db < -45:
                    return jsonify({
                        "success": False,
                        "transcript": "",
                        "status": TRANSCRIPT_NO_SPEECH,
                        "message": (
                            "Your microphone captured silence (audio too quiet). "
                            "Check that the correct mic is selected, it is not muted, "
                            "and no other app (Zoom/Meet/Teams) is holding it."
                        ),
                        "quality": {
                            "duration": (meta.get("audio") or {}).get("duration"),
                            "mean_volume_db": mean_db,
                            "max_volume_db": max_db,
                        }
                    }), 200

            if stt_status == TRANSCRIPT_INVALID:
                msg = (
                    f"Speech recognition produced a garbage/repetitive result ({validation_reason}). "
                    "Please speak more clearly and try again."
                )
            else:
                msg = "No intelligible English speech detected. Speak a little louder and closer to the mic."

            logger.info("[STT] Transcript rejected: status=%s reason=%s", stt_status, validation_reason)
            return jsonify({
                "success": True,   # HTTP-level success; text="" signals no usable speech
                "transcript": "",
                "text": "",        # backward compat field
                "status": stt_status,
                "message": msg,
                "warning": msg,    # backward compat field
                "quality": {
                    "duration": (meta.get("audio") or {}).get("duration"),
                    "sample_rate": (meta.get("audio") or {}).get("sample_rate"),
                    "channels": (meta.get("audio") or {}).get("channels"),
                    "avg_logprob": quality.get("avg_logprob"),
                    "max_no_speech_prob": quality.get("max_no_speech_prob"),
                }
            }), 200

        # LOW_CONFIDENCE: surface to user but don't block — let frontend decide
        # whether to accept it (user can see it and correct if needed).
        logger.info(
            "[STT] Processing done: %dms | status=%s | transcript length=%d chars",
            int((time.time() - t_request) * 1000), stt_status, len(text)
        )

        response_payload = {
            "success": True,
            "transcript": text,
            "text": text,          # backward compat
            "status": stt_status,  # VALID or LOW_CONFIDENCE
            "quality": {
                "duration": (meta.get("audio") or {}).get("duration"),
                "sample_rate": (meta.get("audio") or {}).get("sample_rate"),
                "channels": (meta.get("audio") or {}).get("channels"),
                "avg_logprob": quality.get("avg_logprob"),
                "max_no_speech_prob": quality.get("max_no_speech_prob"),
                "max_compression_ratio": quality.get("max_compression_ratio"),
            },
            "meta": {
                "device": meta.get("device"),
                "model": meta.get("model"),
                "infer_ms": meta.get("infer_ms"),
                "total_ms": meta.get("total_ms"),
            },
        }

        if stt_status == TRANSCRIPT_LOW_CONF:
            response_payload["warning"] = (
                f"Low-confidence transcription ({validation_reason}). "
                "Please review and correct if needed."
            )

        return jsonify(response_payload), 200

    except AudioValidationError as ve:
        logger.warning("[STT ERROR] Audio validation failed: %s", ve)
        return error_response(str(ve), 422)
    except ModelUnavailableError as mue:
        logger.error("[STT ERROR] Whisper model unavailable: %s", mue)
        return error_response(
            "Speech transcription service is temporarily unavailable. Please try again shortly.",
            503,
        )
    except Exception as e:
        # Full technical traceback ONLY in the backend log - never to the client.
        logger.error("[STT ERROR] Unexpected transcription failure: %s\n%s", e, __import__('traceback').format_exc())
        return error_response(
            "Unexpected transcription failure. Full details are available in the backend logs.",
            500,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning("Error deleting temp audio file %s: %s", tmp_path, e)


@gd_bp.route('/agent-response', methods=['POST'])
def get_ai_agent_response():
    """Generate AI agent response using LLM (OpenAI/Groq/Ollama)"""
    user, err = get_authenticated_user()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        
        topic = data.get('topic')
        context = data.get('context', '')
        agent_personality = data.get('agent_personality', 'analytical')
        agent_gender = data.get('agent_gender', 'male')
        # The exact transcription of what the user JUST said - the agent must
        # respond to this, never to stale/cached conversation state.
        latest_user_text = data.get('latest_user_text', '') or ''
        
        if not topic:
            return error_response("Topic is required", 400)
        
        # Generate AI agent response using GDService
        response_text = gd_service.generate_ai_agent_response(
            topic=topic,
            context=context,
            agent_personality=agent_personality,
            agent_gender=agent_gender,
            latest_user_text=latest_user_text
        )

        # Explicit signal when no LLM is configured/reachable: the frontend
        # shows a clear notice instead of the agent speaking unrelated text.
        if response_text == "__AI_UNAVAILABLE__":
            return jsonify({
                "error": "AI agent service is not configured or unreachable. Add a working GOOGLE_API_KEY (or GROQ/OPENAI key) to backend/.env and restart the backend.",
                "agent_response_available": False,
                "success": False
            }), 503

        # Off-topic intervention: when the participant's latest statement is
        # unrelated to the topic, the agent's canonical reply asks them to
        # continue with topic points. The explicit flag lets the frontend hand
        # the floor BACK to the speaker instead of moving the discussion on.
        off_topic_reply = response_text.strip().lower() == GDService.OFF_TOPIC_REPLY.strip().lower()

        return jsonify({
            "response": response_text,
            "off_topic_reply": off_topic_reply,
            "agent_response_available": True,
            "success": True
        }), 200
        
    except Exception as e:
        print(f"AI agent response error: {str(e)}")
        return error_response(f"Failed to generate AI response: {str(e)}", 500)

@gd_bp.route('/schedule', methods=['POST'])
def schedule_gd_round():
    """Admin/Teacher schedules a GD round"""
    user, err = get_authenticated_user()
    if err:
        return err
    
    if user.get("role") not in ["admin", "teacher"]:
        return error_response("Unauthorized: Admin/Teacher privilege required", 403)
        
    try:
        data = request.get_json() or {}
        
        # AI agent count validation
        num_ai_agents = data.get("num_ai_agents", 7)
        if not isinstance(num_ai_agents, int):
            return error_response("num_ai_agents must be an integer", 400)
        if not (MIN_AI_AGENTS <= num_ai_agents <= MAX_AI_AGENTS):
            return error_response("Invalid AI agent count", 400)
            
        # Evaluation criteria validation
        evaluation_criteria = data.get("evaluation_criteria", DEFAULT_EVALUATION_CRITERIA)
        if not isinstance(evaluation_criteria, dict) or not evaluation_criteria:
            return error_response("Invalid evaluation criteria format", 400)
            
        try:
            total_weight = sum(c.get("weight", 0) for c in evaluation_criteria.values())
        except (AttributeError, TypeError):
            return error_response("Invalid criteria weight structure", 400)
            
        if total_weight != 100:
            return error_response("Evaluation weights must total exactly 100", 400)
            
        gd_round = {
            "title": data.get("title", "Group Discussion Round"),
            "scheduled_time": data.get("scheduled_time", datetime.utcnow().isoformat()),
            "duration": data.get("duration", 20),  # minutes
            "topic": data.get("topic"),
            "allow_topic_selection": data.get("allow_topic_selection", False),
            "available_topics": data.get("available_topics", DEFAULT_GD_TOPICS),
            "num_ai_agents": num_ai_agents,
            "ai_agent_voices": data.get("ai_agent_voices", []),  # List of male/female
            "assigned_students": [str(s) for s in data.get("assigned_students", [])],
            "evaluation_criteria": evaluation_criteria,
            "created_by": str(user["_id"]),
            "created_at": datetime.utcnow().isoformat(),
            "status": "scheduled",
            "responses": []
        }
        
        result = gd_rounds_collection.insert_one(gd_round)
        gd_round['_id'] = str(result.inserted_id)
        
        # Create notifications for assigned students
        for student_id in gd_round['assigned_students']:
            notification = {
                "student_id": str(student_id),
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
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/practice-round', methods=['POST'])
def create_practice_round():
    """Any authenticated user (including students) can create a practice GD round"""
    user, err = get_authenticated_user()
    if err:
        return err

    try:
        data = request.get_json() or {}

        num_ai_agents = data.get("num_ai_agents", 7)
        if not isinstance(num_ai_agents, int):
            return error_response("num_ai_agents must be an integer", 400)
        if not (MIN_AI_AGENTS <= num_ai_agents <= MAX_AI_AGENTS):
            return error_response("Invalid AI agent count", 400)

        evaluation_criteria = data.get("evaluation_criteria", DEFAULT_EVALUATION_CRITERIA)
        if not isinstance(evaluation_criteria, dict) or not evaluation_criteria:
            return error_response("Invalid evaluation criteria format", 400)

        try:
            total_weight = sum(c.get("weight", 0) for c in evaluation_criteria.values())
        except (AttributeError, TypeError):
            return error_response("Invalid criteria weight structure", 400)

        if total_weight != 100:
            return error_response("Evaluation weights must total exactly 100", 400)

        gd_round = {
            "title": data.get("title", "Practice GD Round"),
            "scheduled_time": datetime.utcnow().isoformat(),
            "duration": data.get("duration", 20),
            "topic": data.get("topic"),
            "allow_topic_selection": data.get("allow_topic_selection", False),
            "available_topics": data.get("available_topics", DEFAULT_GD_TOPICS),
            "num_ai_agents": num_ai_agents,
            "ai_agent_voices": data.get("ai_agent_voices", []),
            "assigned_students": [str(user["_id"])],
            "evaluation_criteria": evaluation_criteria,
            "created_by": str(user["_id"]),
            "created_at": datetime.utcnow().isoformat(),
            "status": "scheduled",
            "is_practice": True,
            "responses": []
        }

        result = gd_rounds_collection.insert_one(gd_round)
        gd_round['_id'] = str(result.inserted_id)

        return jsonify({
            "message": "Practice GD Round created successfully",
            "gd_round": gd_round,
            "success": True
        }), 201
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to create practice round", 500)

@gd_bp.route('/rounds', methods=['GET'])
def get_gd_rounds():
    """Get all GD rounds for current user role"""
    user, err = get_authenticated_user()
    if err:
        return err
    try:
        user_id_str = str(user["_id"])
        if user.get("role") == "student":
            query = {
                "$or": [
                    {"assigned_students": user_id_str},
                    {"created_by": user_id_str},
                    {"assigned_students": {"$size": 0}}
                ]
            }
            rounds = list(gd_rounds_collection.find(query))
        else:
            rounds = list(gd_rounds_collection.find())
        
        for r in rounds:
            r['_id'] = str(r['_id'])
        
        return jsonify({
            "rounds": rounds,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/student/<student_id>/rounds', methods=['GET'])
def get_student_gd_rounds(student_id):
    """Get GD rounds assigned to a specific student"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    user_id_str = str(user["_id"])
    if user.get("role") == "student" and user_id_str != str(student_id):
        return error_response("Unauthorized access to student rounds", 403)
        
    try:
        rounds = list(gd_rounds_collection.find({
            "$or": [
                {"assigned_students": str(student_id)},
                {"created_by": str(student_id)}
            ]
        }))
        
        for r in rounds:
            r['_id'] = str(r['_id'])
        
        return jsonify({
            "rounds": rounds,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/notifications/<student_id>', methods=['GET'])
def get_student_notifications(student_id):
    """Get GD notifications for a student"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    user_id_str = str(user["_id"])
    if user.get("role") == "student" and user_id_str != str(student_id):
        return error_response("Unauthorized access to notifications", 403)
        
    try:
        notifications = list(gd_notifications_collection.find({
            "student_id": str(student_id)
        }).sort("created_at", -1))
        
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
        
        return jsonify({
            "notifications": notifications,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/notifications/<notification_id>/mark-read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read with ownership validation"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    notif_obj_id, err_resp = validate_object_id(notification_id, "notification ID")
    if err_resp:
        return err_resp
        
    try:
        notification = gd_notifications_collection.find_one({"_id": notif_obj_id})
        if not notification:
            return error_response("Notification not found", 404)
            
        user_id_str = str(user["_id"])
        if user.get("role") == "student" and str(notification.get("student_id")) != user_id_str:
            return error_response("Unauthorized to mark notification", 403)
            
        gd_notifications_collection.update_one(
            {"_id": notif_obj_id},
            {"$set": {"read": True}}
        )
        
        return jsonify({
            "message": "Notification marked as read",
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/round/<round_id>', methods=['GET'])
def get_gd_round_details(round_id):
    """Get details of a specific GD round"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    round_obj_id, err_resp = validate_object_id(round_id)
    if err_resp:
        return err_resp
        
    try:
        gd_round = gd_rounds_collection.find_one({"_id": round_obj_id})
        
        if not gd_round:
            return error_response("GD round not found", 404)
            
        user_id_str = str(user["_id"])
        assigned_students = [str(s) for s in gd_round.get("assigned_students", [])]
        created_by = str(gd_round.get("created_by", ""))
        
        if user.get("role") == "student":
            if assigned_students and user_id_str not in assigned_students and created_by != user_id_str:
                return error_response("Unassigned student cannot access this round", 403)
        
        gd_round['_id'] = str(gd_round['_id'])
        
        return jsonify({
            "round": gd_round,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/round/<round_id>/select-topic', methods=['POST'])
def select_topic(round_id):
    """Student selects a topic from available options"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    round_obj_id, err_resp = validate_object_id(round_id)
    if err_resp:
        return err_resp
        
    try:
        gd_round = gd_rounds_collection.find_one({"_id": round_obj_id})
        if not gd_round:
            return error_response("GD round not found", 404)
            
        user_id_str = str(user["_id"])
        assigned_students = [str(s) for s in gd_round.get("assigned_students", [])]
        created_by = str(gd_round.get("created_by", ""))
        if user.get("role") == "student" and assigned_students and user_id_str not in assigned_students and created_by != user_id_str:
            return error_response("Unassigned student cannot select topic for this round", 403)
            
        if gd_round.get("status") == "completed":
            return error_response("Cannot select topic on completed round", 409)
            
        data = request.get_json() or {}
        selected_topic = data.get("topic")
        
        if not isinstance(selected_topic, str) or not selected_topic.strip():
            return error_response("Invalid topic", 400)
            
        selected_topic = selected_topic.strip()
        available_topics = gd_round.get("available_topics", DEFAULT_GD_TOPICS)
        if selected_topic not in available_topics:
            return error_response("Invalid topic", 400)
        
        gd_rounds_collection.update_one(
            {"_id": round_obj_id},
            {"$set": {"topic": selected_topic, "topic_selected_by": user_id_str}}
        )
        
        return jsonify({
            "message": "Topic selected successfully",
            "topic": selected_topic,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/round/<round_id>/start', methods=['POST'])
def start_gd_round(round_id):
    """Start a GD round"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    round_obj_id, err_resp = validate_object_id(round_id)
    if err_resp:
        return err_resp
        
    try:
        gd_round = gd_rounds_collection.find_one({"_id": round_obj_id})
        if not gd_round:
            return error_response("GD round not found", 404)
            
        user_id_str = str(user["_id"])
        assigned_students = [str(s) for s in gd_round.get("assigned_students", [])]
        created_by = str(gd_round.get("created_by", ""))
        if user.get("role") == "student" and assigned_students and user_id_str not in assigned_students and created_by != user_id_str:
            return error_response("Unassigned student cannot start this round", 403)
            
        if gd_round.get("status") == "completed":
            return error_response("Round is already completed", 409)
            
        gd_rounds_collection.update_one(
            {"_id": round_obj_id},
            {"$set": {
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat(),
                "current_participant": user_id_str
            }}
        )
        
        return jsonify({
            "message": "GD round started",
            "round": {
                "_id": str(gd_round['_id']),
                "topic": gd_round.get('topic'),
                "duration": gd_round.get('duration', 20),
                "num_ai_agents": gd_round.get('num_ai_agents', 7)
            },
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/round/<round_id>/submit-response', methods=['POST'])
def submit_response(round_id):
    """Submit a user's response during GD"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    round_obj_id, err_resp = validate_object_id(round_id)
    if err_resp:
        return err_resp
        
    try:
        gd_round = gd_rounds_collection.find_one({"_id": round_obj_id})
        if not gd_round:
            return error_response("GD round not found", 404)
            
        user_id_str = str(user["_id"])
        assigned_students = [str(s) for s in gd_round.get("assigned_students", [])]
        created_by = str(gd_round.get("created_by", ""))
        if user.get("role") == "student" and assigned_students and user_id_str not in assigned_students and created_by != user_id_str:
            return error_response("Unassigned student cannot submit response for this round", 403)
            
        if gd_round.get("status") == "completed":
            return error_response("Response submitted after round completion", 409)
            
        data = request.get_json() or {}
        response_text = data.get("response_text")
        
        if not isinstance(response_text, str):
            return error_response("response_text must be a string", 400)
            
        response_text = response_text.strip()
        if not response_text:
            return error_response("Response cannot be empty", 400)
            
        if len(response_text) > MAX_RESPONSE_LENGTH:
            return error_response("Response is too long", 400)
            
        response_data = {
            "round_id": str(round_obj_id),
            "student_id": user_id_str,
            "response_text": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "duration": data.get("duration", 0)
        }
        
        gd_rounds_collection.update_one(
            {"_id": round_obj_id},
            {"$push": {"responses": response_data}}
        )
        
        return jsonify({
            "message": "Response submitted",
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/round/<round_id>/evaluate', methods=['POST'])
def evaluate_gd_round(round_id):
    """Evaluate and complete a GD round using stored DB responses"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    round_obj_id, err_resp = validate_object_id(round_id)
    if err_resp:
        return err_resp
        
    try:
        gd_round = gd_rounds_collection.find_one({"_id": round_obj_id})
        if not gd_round:
            return error_response("GD round not found", 404)
            
        user_id_str = str(user["_id"])
        assigned_students = [str(s) for s in gd_round.get("assigned_students", [])]
        created_by = str(gd_round.get("created_by", ""))
        if user.get("role") == "student" and assigned_students and user_id_str not in assigned_students and created_by != user_id_str:
            return error_response("Unassigned student cannot evaluate this round", 403)
            
        # Duplicate evaluation check
        existing_result = gd_results_collection.find_one({
            "round_id": str(round_obj_id),
            "student_id": user_id_str
        })
        if existing_result:
            existing_result['_id'] = str(existing_result['_id'])
            return jsonify({
                "message": "Existing result returned / duplicate prevented",
                "results": existing_result,
                "success": True
            }), 200
            
        # Retrieve stored responses for authenticated student.
        # Only entries whose student_id matches the requesting user are
        # included, so AI-agent messages can never enter the evaluation (they
        # are never submitted through this endpoint anyway).
        stored_responses = gd_round.get("responses", [])
        student_responses = [r for r in stored_responses if str(r.get("student_id")) == user_id_str]
        
        if not student_responses:
            return error_response("Evaluation with no stored student response", 400)

        # Chronological order for evaluation (backend stores push-order which is
        # chronological, but never rely on storage order). Dedupe exact
        # duplicate texts (double-submits) and drop empty entries defensively.
        student_responses.sort(key=lambda r: str(r.get("timestamp") or ""))
        user_contributions = []
        seen_texts = set()
        for r in student_responses:
            txt = str(r.get("response_text") or "").strip()
            if not txt:
                continue  # empty transcripts must never be evaluated
            if txt in seen_texts:
                continue  # duplicate submission - keep exactly one instance
            seen_texts.add(txt)
            user_contributions.append(txt)

        if not user_contributions:
            return error_response("No valid (non-empty) user contribution stored for this round", 400)

        combined_text = " ".join(user_contributions)
        evaluation_criteria = gd_round.get("evaluation_criteria", DEFAULT_EVALUATION_CRITERIA)
        topic = gd_round.get("topic", "General Topic")

        # [EVALUATION_INPUT] audit trail: the exact user contributions of THIS
        # round the evaluator will receive - verifiable against the frontend
        # [TURN n] SUBMIT_DONE logs. AI-agent messages, empties, duplicates and
        # other rounds' data cannot appear here by construction.
        print(f"[EVALUATION_INPUT] Round ID: {str(round_obj_id)}")
        print(f"[EVALUATION_INPUT] Topic: {topic}")
        for i, txt in enumerate(user_contributions, 1):
            print(f'[EVALUATION_INPUT] User contribution {i}: "{txt[:200]}"')
        print(f"[EVALUATION_INPUT] Total user contributions: {len(user_contributions)}")
        
        # Evaluate student response using GDService (LLM-scored when a provider
        # is configured, deterministic content heuristic otherwise).
        student_scores_dict = gd_service.evaluate_participant_response(combined_text, evaluation_criteria, topic)
        evaluation_method = student_scores_dict.pop("evaluation_method", "heuristic")
        # Strict topic-relevance gate: if the speech is NOT related to the topic,
        # every criterion is hard-capped at 5 so an off-topic answer can never
        # earn a passing score. This mirrors/enforces what the LLM was instructed
        # to do (and what the heuristic already does).
        topic_related = bool(student_scores_dict.pop("topic_related", False))
        # LLM per-criterion detail: {crit: {score, evidence, reason}}. Used to
        # surface the evaluator's quoted evidence and reasoning in the results
        # screen so scores are transparent (not random numbers).
        llm_detail = student_scores_dict.pop("_llm_detail", None) or {}
        if not topic_related:
            for crit_key in evaluation_criteria.keys():
                if crit_key in student_scores_dict:
                    try:
                        student_scores_dict[crit_key] = min(float(student_scores_dict[crit_key]), 5.0)
                    except (TypeError, ValueError):
                        student_scores_dict[crit_key] = 5.0
            print(f"[SCORE_VALIDATION] Topic-relevance gate applied: content NOT related to topic -> all criterion scores capped at 5")

        def _clamp_score(value):
            """Coerce an LLM score to a sane number in [0, 100]."""
            try:
                value = float(value)
            except (TypeError, ValueError):
                return 0.0
            return max(0.0, min(100.0, value))

        formatted_student_scores = {}
        for crit_key, crit_val in evaluation_criteria.items():
            raw_score = _clamp_score(student_scores_dict.get(crit_key, 0))
            weight = crit_val.get("weight", 20)
            formatted_student_scores[crit_key] = {"score": raw_score, "weight": weight}

        # Per-criterion feedback (evidence quote + reason) for the results UI.
        criterion_feedback = {}
        for crit_key in evaluation_criteria.keys():
            detail = llm_detail.get(crit_key) if isinstance(llm_detail, dict) else None
            if isinstance(detail, dict) and (detail.get("evidence") or detail.get("reason")):
                evidence = str(detail.get("evidence") or "none").strip()
                reason = str(detail.get("reason") or "").strip()
                if not topic_related and not reason:
                    reason = "Speech was not related to the topic, so no relevant content was found for this criterion."
                criterion_feedback[crit_key] = {"evidence": evidence, "reason": reason}
        if not criterion_feedback and not topic_related:
            # Heuristic mode + off-topic: honest deterministic feedback
            for crit_key in evaluation_criteria.keys():
                criterion_feedback[crit_key] = {
                    "evidence": "none",
                    "reason": "Your speech was not related to the topic, so no relevant content could be found for this criterion.",
                }

        student_total_score = sum(
            (formatted_student_scores[k]["score"] * formatted_student_scores[k]["weight"]) / 100
            for k in formatted_student_scores
        )

        # ---- Score validation ----
        ok, validation_errors, computed_total = validate_score_result(
            formatted_student_scores, evaluation_criteria, combined_text
        )
        if not ok:
            print(f"[SCORE_VALIDATION] Errors: {validation_errors}")
            # Don't reject outright: log and continue with clamped values
        # Re-derive total from validated clamped scores (prevents math drift)
        student_total_score = computed_total
        
        participants = []
        participants.append({
            "id": user_id_str,
            "name": user.get("name", "You"),
            "type": "student",
            "scores": formatted_student_scores,
            "total_score": round(student_total_score, 2),
            "rank": 0
        })
        
        # Generate AI agent scores
        num_ai_agents = gd_round.get("num_ai_agents", 7)
        for i in range(num_ai_agents):
            ai_score_data = generate_ai_agent_score(
                evaluation_criteria,
                agent_id=f"ai_agent_{i+1}",
                round_id=str(round_obj_id)
            )
            participants.append({
                "id": f"ai_agent_{i+1}",
                "name": f"AI Agent {i+1}",
                "type": "ai",
                "scores": ai_score_data["scores"],
                "total_score": ai_score_data["total_score"],
                "rank": 0
            })
            
        participants.sort(key=lambda x: x["total_score"], reverse=True)
        for idx, participant in enumerate(participants):
            participant["rank"] = idx + 1
            
        top_3 = participants[:3]
        student_rank = next((p["rank"] for p in participants if p["type"] == "student"), 1)
        
        result = {
            "round_id": str(round_obj_id),
            "student_id": user_id_str,
            "all_participants": participants,
            "top_3": top_3,
            "student_rank": student_rank,
            "evaluation_criteria": evaluation_criteria,
            "evaluation_method": evaluation_method,
            "topic_related": topic_related,
            "criterion_feedback": criterion_feedback,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        insert_res = gd_results_collection.insert_one(result)
        result['_id'] = str(insert_res.inserted_id)
        
        gd_rounds_collection.update_one(
            {"_id": round_obj_id},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }}
        )
        
        return jsonify({
            "message": "GD round evaluated successfully",
            "results": result,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

@gd_bp.route('/results/<student_id>', methods=['GET'])
def get_student_results(student_id):
    """Get all GD results for a student"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    user_id_str = str(user["_id"])
    if user.get("role") == "student" and user_id_str != str(student_id):
        return error_response("Unauthorized access to results", 403)
        
    try:
        results = list(gd_results_collection.find({
            "student_id": str(student_id)
        }).sort("completed_at", -1))
        
        for result in results:
            result['_id'] = str(result['_id'])
        
        return jsonify({
            "results": results,
            "success": True
        }), 200
    except Exception as e:
        print(f"GD error: {str(e)}")
        return error_response("Unable to process GD request", 500)

def validate_score_result(formatted_scores, criteria, combined_text):
    """Validate that every criterion has a score in range, and the weighted
    total is mathematically consistent.  Returns (ok: bool, errors: list[str])."""
    errors = []
    computed_total = 0.0
    for k, criterion_data in criteria.items():
        if k not in formatted_scores:
            errors.append(f"Missing score for criterion: {k}")
            continue
        s = formatted_scores[k].get("score", -1)
        w = formatted_scores[k].get("weight", criterion_data.get("weight", 0))
        if not isinstance(s, (int, float)) or not (0 <= s <= 100):
            errors.append(f"Score out of range for {k}: {s}")
        computed_total += (float(s) * float(w)) / 100.0
    return len(errors) == 0, errors, round(computed_total, 2)


def generate_ai_agent_score(criteria, agent_id=None, round_id=None):
    """Generate AI agent scores using a seeded normal distribution so scores
    are deterministic for a given (agent_id, round_id) pair — same round always
    produces the same AI ranking.  Mean ≈ 72, std ≈ 9 approximates a realistic
    bell curve for good-but-not-exceptional GD performance.

    This is explicitly SIMULATED because AI agents do not have real transcripts;
    it is documented as such and NOT random each call.
    """
    import hashlib
    seed_str = f"{agent_id or 'ai'}:{round_id or 'round'}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (2**31)

    import random as _rand_mod
    rng = _rand_mod.Random(seed)

    scores = {}
    for criterion_key, criterion_data in criteria.items():
        # Normal distribution with mean=72, std=9, clamped [45, 92]
        base = rng.gauss(72, 9)
        base = max(45.0, min(92.0, base))
        scores[criterion_key] = {
            "score": round(base, 1),
            "weight": criterion_data["weight"],
            "simulated": True,   # explicit audit flag
        }

    total_score = sum(
        (scores[k]["score"] * scores[k]["weight"]) / 100
        for k in scores
    )

    return {
        "scores": scores,
        "total_score": round(total_score, 2),
    }

@gd_bp.route('/admin/config', methods=['GET', 'POST'])
def gd_admin_config():
    """Get or update GD configuration"""
    user, err = get_authenticated_user()
    if err:
        return err
        
    if user.get("role") not in ["admin", "teacher"]:
        return error_response("Unauthorized: Admin configuration access required", 403)
        
    if request.method == 'GET':
        return jsonify({
            "default_topics": DEFAULT_GD_TOPICS,
            "evaluation_criteria": DEFAULT_EVALUATION_CRITERIA,
            "default_duration": 20,
            "min_ai_agents": MIN_AI_AGENTS,
            "max_ai_agents": MAX_AI_AGENTS,
            "success": True
        }), 200
    else:
        try:
            data = request.get_json() or {}
            crit = data.get("evaluation_criteria")
            if crit:
                try:
                    total_weight = sum(c.get("weight", 0) for c in crit.values())
                    if total_weight != 100:
                        return error_response("Evaluation weights must total exactly 100", 400)
                except (AttributeError, TypeError):
                    return error_response("Invalid evaluation criteria format", 400)
                    
            return jsonify({
                "message": "Configuration updated successfully",
                "success": True
            }), 200
        except Exception as e:
            print(f"GD error: {str(e)}")
            return error_response("Unable to process GD request", 500)
