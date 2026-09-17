import os
import threading
from dotenv import load_dotenv
import google.generativeai as genai
from app import create_app
from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS # Added to handle CORS errors

# 1. Load the .env file to get the Google API Key
load_dotenv()

# 2. Configure Google AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Helper function to find a working model for the single /ask-ai route
def generate_safe_response(prompt):
    candidates = ['gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-flash-latest', 'gemini-pro-latest']
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text') and response.text and len(response.text.strip()) >= 15:
                return response.text
            continue
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            return f"Error: {str(e)}"
    return "Error: No AI models available. Check your API key."

app = create_app()
# CORS is already configured in create_app() with credentials support

# Preload the Whisper STT model in the background so the first /api/gd/transcribe
# request doesn't stall for 30-60s (model download + init) while the frontend is
# waiting on a speaking turn. The preload retries: transient network failures
# during a HuggingFace model download (WinError 10053/10060) previously left the
# app with no model and every transcribe call failing.
import time

def _preload_whisper(retries=3, delay_seconds=5):
    for attempt in range(1, retries + 1):
        try:
            from app.services.stt_service import stt_service
            stt_service.load_model()
            stt_service.warmup()
            print("[STT] Whisper model preloaded and warmed up.")
            return
        except Exception as e:
            print(f"[STT] Whisper preload attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay_seconds)
    print("[STT] Whisper preload skipped - model will load lazily on first request.")

threading.Thread(target=_preload_whisper, daemon=True).start()

# Use environment variable for secret key, generate random one if not set
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

DEMO_CREDENTIALS = {
    'admin': 'password',
    'teacher': 'password', 
    'student': 'password',
    'hr': 'password'
}

@app.route('/')
def index():
    if 'user_role' in session:
        return redirect(url_for(f'{session["user_role"]}_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').lower()
    password = data.get('password', '')
    
    if username in DEMO_CREDENTIALS and DEMO_CREDENTIALS[username] == password:
        session['user_role'] = username
        session['username'] = username
        
        # Generate JWT token for demo user
        from app.routes.auth_routes import generate_jwt_token
        token = generate_jwt_token(username, f"{username}@demo.com", username)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': username,
                'name': username.capitalize(),
                'email': f"{username}@demo.com",
                'role': username
            },
            'redirect': f'/{username}'
        })
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/admin')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    return render_template('index.html', role='admin')

@app.route('/student')
def student_dashboard():
    if session.get('user_role') != 'student':
        return redirect(url_for('index'))
    return render_template('index.html', role='student')

@app.route('/teacher')
def teacher_dashboard():
    if session.get('user_role') != 'teacher':
        return redirect(url_for('index'))
    return render_template('index.html', role='teacher')

@app.route('/hr')
def hr_dashboard():
    if session.get('user_role') != 'hr':
        return redirect(url_for('index'))
    return render_template('index.html', role='hr')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/resumes/<filename>')
def serve_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files like logo"""
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_folder, filename)

@app.route('/uploads/submissions/<assignment_id>/<filename>')
def serve_submission(assignment_id, filename):
    """Serve submitted assignment files"""
    submission_path = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', assignment_id)
    return send_from_directory(submission_path, filename)

# --- UPDATED AI ROUTE ---
@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    if 'user_role' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')

        if not user_prompt:
            return jsonify({'success': False, 'message': 'No prompt provided'})

        # Use the safe generator that tries multiple models
        response_text = generate_safe_response(user_prompt)
        
        return jsonify({
            'success': True, 
            'response': response_text
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # use_reloader=False: the Werkzeug reloader imports this module in TWO
    # processes (parent + child), which used to download/load the Whisper model
    # twice and spam 'OSError: [WinError 10038]' socket noise on every restart.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)