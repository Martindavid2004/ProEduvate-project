from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os

def create_app():
    backend_root = os.path.dirname(os.path.dirname(__file__))  # …/backend
    app = Flask(
        __name__,
        template_folder=os.path.join(backend_root, 'templates'),
        static_folder=os.path.join(backend_root, 'static')
    )
    
    # Configure CORS to allow requests from localhost and Netlify
    CORS(app, supports_credentials=True)

    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

    UPLOAD_FOLDER = os.path.join(backend_root, 'uploads', 'resumes')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # blueprints
    from .routes.admin_routes import admin_bp
    from .routes.teacher_routes import teacher_bp
    from .routes.student_routes import student_bp
    from .routes.hr_routes import hr_bp
    from .routes.interview_routes import interview_bp
    from .routes.chatbot_routes import chatbot_bp
    from .routes.auth_routes import auth_bp
    from .routes.aptitude_routes import aptitude_bp
    from .routes.gd_routes import gd_bp
    from .routes.skill_routes import skill_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(aptitude_bp)
    app.register_blueprint(gd_bp)
    app.register_blueprint(skill_bp)

    # Skill Card System duplicate-prevention indexes (idempotent). The
    # service layer also guards every award, so a skipped index never
    # breaks the feature.
    from .database import ensure_skill_indexes
    try:
        ensure_skill_indexes()
    except Exception as e:
        print(f"Warning: could not create skill indexes: {e}")

    # Unique per-attempt indexes: make assessment start race-proof so a
    # double start / two tabs / refresh can never create two attempts for
    # the same assessment+student pair (BUG 5/6/9). Idempotent.
    from .services.assessment_state import ensure_attempt_indexes
    try:
        ensure_attempt_indexes()
    except Exception as e:
        print(f"Warning: could not create assessment attempt indexes: {e}")

    @app.route('/resumes/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def root():
        return jsonify({
            "status": "online",
            "app": "ProEduVate LMS Backend API",
            "health": "/api/health"
        }), 200

    @app.route('/health')
    def health_check():
        return "Server is running!", 200
    
    @app.route('/api/health')
    def api_health_check():
        return jsonify({"status": "ok", "message": "API is running"}), 200

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "error": "Endpoint not found",
            "message": "The requested API endpoint does not exist."
        }), 404

    return app

