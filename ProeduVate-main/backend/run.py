import os
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
    candidates = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.5-pro', 'gemini-pro-latest']
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            return f"Error: {str(e)}"
    return "Error: No AI models available. Check your API key."

app = create_app()
# Enable CORS for all routes to prevent 200 OK OPTIONS but failed POST errors
CORS(app) 

app.secret_key = 'AIzaSyDK_V5WbHRElHthkrTUC_SnWJy4RzYvF7k'

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
        return jsonify({'success': True, 'redirect': f'/{username}'})
    
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
    app.run(host='0.0.0.0', port=5001, debug=True)