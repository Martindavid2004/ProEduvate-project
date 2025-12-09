# student_routes.py

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from ..database import assignments_collection, users_collection, teacher_assignments_collection, submissions_collection
from ..models.assignment import assignment_helper
from bson import ObjectId
from werkzeug.utils import secure_filename
import os
from ..services.ai_service import extract_text_from_pdf, get_ats_analysis

student_bp = Blueprint('student_bp', __name__, url_prefix='/api/student')

# Storage for quiz submissions (can be moved to DB later)
quiz_submissions = {}
student_notifications = []

def allowed_file(filename):
    # Allowed extensions for resume uploads
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

def allowed_assignment_file(filename):
    # Broader allowed extensions for general assignment uploads
    allowed_extensions = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'zip', 'rar'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@student_bp.route('/assignments', methods=['GET'])
def get_student_assignments():
    """Get all assignments available to students"""
    try:
        # Get both admin-assigned and teacher-created assignments
        admin_assignments = list(assignments_collection.find({"createdBy": "admin"}))
        teacher_assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        
        all_assignments = []
        
        # Process admin assignments
        for a in admin_assignments:
            all_assignments.append({
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "dueDate": a.get("dueDate"),
                "type": a.get("type", "manual"),
                "createdBy": "admin",
                "isNew": a.get('createdAt', '') > get_last_login_time()
            })
        
        # Process teacher assignments
        for a in teacher_assignments:
            all_assignments.append({
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "dueDate": a["dueDate"],
                "type": a.get("type", "manual"),
                "createdBy": "teacher",
                "isNew": a.get('createdAt', '') > get_last_login_time()
            })
        
        return jsonify(all_assignments), 200
    except Exception as e:
        print(f"Error fetching student assignments: {e}")
        return jsonify({"error": "Failed to fetch assignments"}), 500

# This route remains unchanged
@student_bp.route('/<user_id>/upload_resume', methods=['POST'])
def upload_resume(user_id):
    if 'resume' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['resume']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or no file selected"}), 400

    filename = secure_filename(f"{user_id}_{file.filename}")
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    resume_text = extract_text_from_pdf(save_path)
    if not resume_text:
        return jsonify({"error": "Could not read text from PDF"}), 500

    job_description = """
    Job Title: Junior Fullstack Java Developer
    Responsibilities:
    - Develop and maintain web applications using Java, Spring Boot, and React.js.
    - Create REST APIs and integrate with front-end components.
    - Work with MySQL databases to design schemas and write efficient queries.
    Qualifications:
    - Experience with Java and the Spring Boot framework.
    - Familiarity with front-end technologies like React.js, HTML, and CSS.
    - Knowledge of REST APIs and MySQL.
    """

    ats_analysis = get_ats_analysis(resume_text, job_description)

    if not ats_analysis:
        return jsonify({"error": "Failed to get analysis from AI model. Ensure Ollama is running."}), 500

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": { "resume_filename": filename, "atsScore": ats_analysis.get("match_score") }}
    )
    
    return jsonify(ats_analysis), 200

# --- [FIXED CODE] ---
# This entire route has been rewritten to handle file uploads for assignments.
@student_bp.route('/assignments/<assignment_id>/submit', methods=['POST'])
def submit_assignment(assignment_id):
    """Submit an assignment file"""
    try:
        # 1. Check if the file is part of the request
        if 'assignment_file' not in request.files:
            return jsonify({"error": "No assignment_file part in the request"}), 400

        file = request.files['assignment_file']
        student_id = request.form.get('student_id')
        notes = request.form.get('notes', '') # Get notes, default to empty string

        # 2. Validate the file and student ID
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not student_id:
            return jsonify({"error": "Missing student_id"}), 400

        if file and allowed_assignment_file(file.filename):
            # 3. Create a secure filename and define a save path
            filename = secure_filename(file.filename)
            
            # Create a dedicated folder for submissions if it doesn't exist
            # The path will be something like: uploads/submissions/<assignment_id>/
            submission_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', assignment_id)
            os.makedirs(submission_folder, exist_ok=True)
            
            # Define the final path to save the file
            save_path = os.path.join(submission_folder, f"{student_id}_{filename}")
            
            # 4. Save the file to the server's file system
            file.save(save_path)

            # 5. Save the submission record to MongoDB
            submission_record = {
                "assignment_id": assignment_id,
                "student_id": student_id,
                "filename": filename,
                "file_path": f"/uploads/submissions/{assignment_id}/{student_id}_{filename}",
                "notes": notes,
                "submitted_at": datetime.now()
            }
            
            # Check if student already submitted this assignment, update if exists
            existing = submissions_collection.find_one({
                "assignment_id": assignment_id,
                "student_id": student_id
            })
            
            if existing:
                submissions_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": submission_record}
                )
            else:
                submissions_collection.insert_one(submission_record)

            return jsonify({
                "message": "Assignment submitted successfully!",
                "filename": filename,
                "submission": {
                    "assignment_id": assignment_id,
                    "student_id": student_id,
                    "filename": filename,
                    "submitted_at": submission_record["submitted_at"].isoformat()
                }
            }), 200
        else:
            return jsonify({"error": "File type not allowed"}), 400

    except Exception as e:
        # Use a more accurate error message
        print(f"Error submitting assignment: {e}")
        return jsonify({"error": "Failed to submit assignment"}), 500

# This route remains unchanged
@student_bp.route('/assignments/<assignment_id>/quiz', methods=['GET'])
def get_assignment_quiz(assignment_id):
    """Get quiz questions for a specific assignment"""
    try:
        # Try to find in teacher assignments collection
        assignment = teacher_assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        
        if assignment and assignment.get('questions'):
            return jsonify({"questions": assignment['questions']}), 200
        else:
            return jsonify({"error": "Quiz not found"}), 404
    except Exception as e:
        print(f"Error fetching assignment quiz: {e}")
        return jsonify({"error": "Failed to fetch quiz"}), 500

@student_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for students"""
    try:
        notifications = []
        # Get quiz assignments from teacher assignments
        quiz_assignments = list(teacher_assignments_collection.find({"type": "quiz"}))
        
        for assignment in quiz_assignments:
            notifications.append({
                "id": f"quiz_{str(assignment['_id'])}",
                "type": "quiz",
                "title": f"New Quiz: {assignment['title']}",
                "message": f"A new quiz '{assignment['title']}' has been assigned. Due: {assignment['dueDate']}",
                "assignment_id": str(assignment['_id']),
                "created_at": assignment.get('createdAt')
            })
        notifications.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify(notifications), 200
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({"error": "Failed to fetch notifications"}), 500

def get_last_login_time():
    """Mock function to get last login time"""
    return "2024-01-01T00:00:00"

@student_bp.route('/<student_id>/submissions', methods=['GET'])
def get_student_submissions(student_id):
    """Get all submissions for a specific student"""
    try:
        submissions = list(submissions_collection.find({"student_id": student_id}))
        student_submissions = []
        for sub in submissions:
            student_submissions.append({
                "id": str(sub["_id"]),
                "assignment_id": sub["assignment_id"],
                "student_id": sub["student_id"],
                "filename": sub["filename"],
                "file_path": sub["file_path"],
                "notes": sub.get("notes", ""),
                "submitted_at": sub["submitted_at"].isoformat()
            })
        return jsonify(student_submissions), 200
    except Exception as e:
        print(f"Error fetching student submissions: {e}")
        return jsonify({"error": "Failed to fetch submissions"}), 500