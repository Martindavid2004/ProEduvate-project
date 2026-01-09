# student_routes.py

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from ..database import assignments_collection, users_collection, teacher_assignments_collection, submissions_collection
from ..models.assignment import assignment_helper
from bson import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from ..services.ai_service import extract_text_from_pdf, get_ats_analysis
from ..services.lambda_service import execute_python_code_lambda

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

@student_bp.route('/<user_id>/assignments', methods=['GET'])
def get_student_assignments_by_id(user_id):
    """Get assignments for a specific student"""
    try:
        # Students should only see teacher-created assignments
        # Admin assignments are tasks assigned to teachers, not students
        teacher_assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        
        all_assignments = []
        
        # Process teacher assignments only
        for a in teacher_assignments:
            assignment_id = str(a["_id"])
            # Check if student has submitted this assignment
            submission = submissions_collection.find_one({
                "assignment_id": assignment_id,
                "student_id": user_id
            })
            
            assignment_data = {
                "id": assignment_id,
                "title": a["title"],
                "description": a["description"],
                "dueDate": a["dueDate"],
                "type": a.get("type", "manual"),
                "createdBy": "teacher",
                "submitted": submission is not None,
                "submittedAt": submission.get("submitted_at").isoformat() if submission and submission.get("submitted_at") else None,
                "status": "submitted" if submission else "pending"
            }
            
            # Add quiz-specific data
            if a.get("type") == "Quiz" and a.get("quizQuestions"):
                assignment_data["quiz_questions"] = a["quizQuestions"]
            
            # Add quiz score if submitted
            if submission and submission.get("quiz_score"):
                assignment_data["quiz_score"] = submission["quiz_score"]
            
            all_assignments.append(assignment_data)
        
        return jsonify(all_assignments), 200
    except Exception as e:
        print(f"Error fetching student assignments: {e}")
        return jsonify({"error": "Failed to fetch assignments"}), 500

@student_bp.route('/<user_id>/progress', methods=['GET'])
def get_student_progress(user_id):
    """Get progress data for a specific student"""
    try:
        # Get student information
        # Try to find user by _id as ObjectId or by integer id field
        student = None
        try:
            student = users_collection.find_one({"_id": ObjectId(user_id)})
        except:
            # If ObjectId conversion fails, try finding by integer id
            try:
                student = users_collection.find_one({"id": int(user_id)})
            except:
                student = users_collection.find_one({"id": user_id})
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        # Calculate progress metrics
        total_assignments = assignments_collection.count_documents({}) + teacher_assignments_collection.count_documents({})
        completed_assignments = submissions_collection.count_documents({"student_id": user_id})
        
        # Get quiz-specific data
        quiz_submissions = list(submissions_collection.find({
            "student_id": user_id,
            "quiz_score": {"$exists": True}
        }))
        
        avg_quiz_score = 0
        if quiz_submissions:
            avg_quiz_score = sum(sub.get("quiz_score", 0) for sub in quiz_submissions) / len(quiz_submissions)
        
        progress = {
            "totalAssignments": total_assignments,
            "completedAssignments": completed_assignments,
            "submittedAssignments": completed_assignments,
            "completionRate": (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0,
            "averageScore": student.get("average_score", 0),
            "attendanceRate": student.get("attendance", 95),
            "resumeScore": student.get("resumeScore"),
            "interviewScore": student.get("interviewScore"),
            "quizScore": avg_quiz_score if avg_quiz_score > 0 else student.get("quizScore"),
            "averageQuizScore": avg_quiz_score if avg_quiz_score > 0 else student.get("averageQuizScore"),
            "totalQuizzes": len(quiz_submissions),
            "recentActivity": [
                {"date": "2024-12-14", "activity": "Submitted assignment"},
                {"date": "2024-12-13", "activity": "Completed quiz"}
            ]
        }
        
        return jsonify(progress), 200
    except Exception as e:
        print(f"Error fetching student progress: {e}")
        return jsonify({"error": "Failed to fetch progress"}), 500

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

    # Extract the score - try different possible keys
    resume_score = ats_analysis.get("match_score") or ats_analysis.get("score") or ats_analysis.get("overall_score")
    matching_keywords = ats_analysis.get("matching_keywords") or []
    missing_keywords = ats_analysis.get("missing_keywords") or []
    summary = ats_analysis.get("summary") or ""
    
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": { 
            "resume_filename": filename, 
            "atsScore": resume_score,
            "resumeScore": resume_score,
            "matchingSkills": matching_keywords,
            "missingSkills": missing_keywords,
            "resumeSummary": summary
        }}
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
        quiz_score = request.form.get('quiz_score')  # Get quiz score if provided

        # 2. Validate the file and student ID
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not student_id:
            return jsonify({"error": "Missing student_id"}), 400

        if file and (allowed_assignment_file(file.filename) or file.filename.endswith('.json')):
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
            
            # Add quiz score if provided
            if quiz_score:
                submission_record["quiz_score"] = float(quiz_score)
            
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
            
            # Update student's submission count and quiz scores in users collection
            total_submissions = submissions_collection.count_documents({"student_id": student_id})
            update_data = {"submittedAssignments": total_submissions}
            
            # If this is a quiz submission, update quiz-related scores
            if quiz_score:
                # Calculate average quiz score from all quiz submissions
                quiz_submissions_list = list(submissions_collection.find({
                    "student_id": student_id,
                    "quiz_score": {"$exists": True}
                }))
                
                if quiz_submissions_list:
                    avg_quiz_score = sum(sub.get("quiz_score", 0) for sub in quiz_submissions_list) / len(quiz_submissions_list)
                    update_data["quizScore"] = avg_quiz_score
                    update_data["averageQuizScore"] = avg_quiz_score
            
            users_collection.update_one(
                {"_id": ObjectId(student_id)},
                {"$set": update_data}
            )

            return jsonify({
                "message": "Assignment submitted successfully!",
                "filename": filename,
                "submission": {
                    "assignment_id": assignment_id,
                    "student_id": student_id,
                    "filename": filename,
                    "submitted_at": submission_record["submitted_at"].isoformat(),
                    "quiz_score": quiz_score
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


@student_bp.route('/execute-code', methods=['POST'])
def execute_code():
    """Execute Python code using AWS Lambda"""
    try:
        data = request.get_json()
        
        # Get code and input from request
        source_code = data.get('source_code', '')
        stdin_input = data.get('stdin', '')
        base64_encoded = data.get('base64_encoded', False)
        
        # Debug: Print what we received
        print(f"Received stdin (base64): {stdin_input[:50] if stdin_input else 'EMPTY'}")
        
        # Use AWS Lambda service to execute code
        result = execute_python_code_lambda(source_code, stdin_input, base64_encoded)
        
        return jsonify(result), 200
    
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        import base64
        return jsonify({
            "stdout": None,
            "stderr": base64.b64encode(error_msg.encode()).decode() if data.get('base64_encoded') else error_msg,
            "status": {"id": 13, "description": "Internal Error"},
            "time": None,
            "memory": None,
            "message": base64.b64encode(error_msg.encode()).decode() if data.get('base64_encoded') else error_msg
        }), 200

@student_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change student password"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not all([student_id, current_password, new_password]):
            return jsonify({'message': 'All fields are required'}), 400

        # Find the student
        student = users_collection.find_one({'_id': ObjectId(student_id)})
        
        if not student:
            return jsonify({'message': 'Student not found'}), 404

        # Verify current password
        if not check_password_hash(student.get('password', ''), current_password):
            return jsonify({'message': 'Current password is incorrect'}), 401

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update the password
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {'password': hashed_password}}
        )

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return jsonify({'message': 'Failed to change password'}), 500

@student_bp.route('/update-profile', methods=['POST'])
def update_profile():
    """Update student profile information"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name')
        email = data.get('email')
        department = data.get('department')

        if not all([student_id, name, email, department]):
            return jsonify({'message': 'All fields are required'}), 400

        # Check if email is already used by another user
        existing_user = users_collection.find_one({
            'email': email,
            '_id': {'$ne': ObjectId(student_id)}
        })
        
        if existing_user:
            return jsonify({'message': 'Email already in use by another account'}), 400

        # Update the profile
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {
                'name': name,
                'email': email,
                'department': department
            }}
        )

        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        return jsonify({'message': 'Failed to update profile'}), 500

@student_bp.route('/update-notifications', methods=['POST'])
def update_notifications():
    """Update student notification preferences"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        email_notifications = data.get('email_notifications', True)
        assignment_notifications = data.get('assignment_notifications', True)
        interview_notifications = data.get('interview_notifications', True)

        if not student_id:
            return jsonify({'message': 'Student ID is required'}), 400

        # Update notification preferences
        users_collection.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {
                'notifications': {
                    'email': email_notifications,
                    'assignments': assignment_notifications,
                    'interviews': interview_notifications
                }
            }}
        )

        return jsonify({'message': 'Notification preferences updated successfully'}), 200

    except Exception as e:
        print(f"Error updating notifications: {str(e)}")
        return jsonify({'message': 'Failed to update notification preferences'}), 500

