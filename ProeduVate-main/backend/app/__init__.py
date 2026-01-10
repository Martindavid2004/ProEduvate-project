# lms_portal_backend/app/__init__.py
from flask import Flask, send_from_directory, jsonify
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
    CORS(app, 
         resources={r"/*": {
             "origins": [
                 "http://localhost:3000",
                 "http://127.0.0.1:3000",
                 "https://proeduvate.netlify.app",
                 "https://*.netlify.app"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }})

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

    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(interview_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(aptitude_bp)

    @app.route('/resumes/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/health')
    def health_check():
        return "Server is running!", 200
    
    @app.route('/api/health')
    def api_health_check():
        return jsonify({"status": "ok", "message": "API is running"}), 200

    return app

