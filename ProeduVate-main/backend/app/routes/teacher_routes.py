# lms_portal_backend/app/routes/teacher_routes.py

from flask import Blueprint, request, jsonify
from ..database import users_collection, assignments_collection, teacher_assignments_collection, submissions_collection
from ..models.user import user_helper
from ..services.ai_service import get_ai_response
from bson import ObjectId
import uuid
from datetime import datetime

teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/api/teacher')

# In-memory storage for quiz questions (can be moved to DB later if needed)
quiz_questions_storage = {}

@teacher_bp.route('/students/progress', methods=['GET'])
def get_student_progress():
    students = users_collection.find({"role": "student"})
    student_list = []
    
    for student in students:
        student_id = str(student["_id"])
        # Get submission count for this student
        submission_count = submissions_collection.count_documents({"student_id": student_id})
        
        # Update student record with submission count
        users_collection.update_one(
            {"_id": student["_id"]},
            {"$set": {"submittedAssignments": submission_count}}
        )
        
        student_list.append(user_helper(student, submission_count))
    
    return jsonify(student_list)

@teacher_bp.route('/assignments', methods=['POST'])
def create_assignment():
    """Create a new assignment"""
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('dueDate', datetime.now().isoformat())
        assignment_type = data.get('type', 'Assignment')
        quiz_questions = data.get('quizQuestions')
        
        if not all([title, description]):
            return jsonify({"error": "Missing required fields"}), 400
        
        assignment = {
            "title": title,
            "description": description,
            "dueDate": due_date,
            "type": assignment_type,
            "createdBy": "teacher",
            "createdAt": datetime.now().isoformat()
        }
        
        # Store quiz questions directly in the assignment document
        if quiz_questions:
            assignment["quizQuestions"] = quiz_questions
        
        # Save to MongoDB
        result = teacher_assignments_collection.insert_one(assignment)
        assignment_id = str(result.inserted_id)
        
        # Also store in memory for backward compatibility
        if quiz_questions:
            quiz_questions_storage[assignment_id] = quiz_questions
        
        return jsonify({
            "message": "Assignment created successfully",
            "assignment_id": assignment_id
        }), 201
        
    except Exception as e:
        print(f"Error creating assignment: {e}")
        return jsonify({"error": "Failed to create assignment"}), 500

def generate_quiz_questions(title, description):
    try:
        topic = f"{title}. {description}"
        prompt = f"""
        Create a quiz based on this topic: {topic}
        Generate exactly 5 multiple-choice questions.
        IMPORTANT: Your entire response must be a single, raw JSON object.
        The JSON object must have a single key "questions".
        The value of "questions" must be a list of exactly 5 question objects.
        Each question object must have: "question", "options" (list of 4), "correct_answer".
        """
        ai_response = get_ai_response(prompt)
        if ai_response and "questions" in ai_response:
            return ai_response["questions"]
        return None
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        return None

@teacher_bp.route('/assignments', methods=['GET'])
def get_teacher_assignments():
    """Get all assignments created by teachers"""
    try:
        assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        teacher_assignments = []
        for a in assignments:
            teacher_assignments.append({
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "dueDate": a["dueDate"],
                "type": a.get("type", "manual"),
                "createdBy": a["createdBy"],
                "createdAt": a.get("createdAt"),
                "questions": a.get("questions")
            })
        return jsonify(teacher_assignments), 200
    except Exception as e:
        print(f"Error fetching teacher assignments: {e}")
        return jsonify({"error": "Failed to fetch assignments"}), 500

@teacher_bp.route('/assignments/<assignment_id>/questions', methods=['GET'])
def get_quiz_questions(assignment_id):
    try:
        if assignment_id in quiz_questions_storage:
            return jsonify({"questions": quiz_questions_storage[assignment_id]}), 200
        else:
            return jsonify({"error": "Quiz questions not found"}), 404
    except Exception as e:
        print(f"Error fetching quiz questions: {e}")
        return jsonify({"error": "Failed to fetch quiz questions"}), 500

@teacher_bp.route('/admin-assignments/<teacher_id>', methods=['GET'])
def get_admin_assignments(teacher_id):
    try:
        query = {"teacherId": ObjectId(teacher_id), "createdBy": "admin"}
        assignments = list(assignments_collection.find(query))
        results = []
        for a in assignments:
            results.append({
                "id": str(a['_id']),
                "title": a['title'],
                "description": a['description'],
                "status": a.get('status', 'Pending'),
                "dueDate": a.get('dueDate'),
                "createdBy": "admin"
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@teacher_bp.route('/admin_tasks', methods=['GET'])
def get_admin_tasks():
    """Get tasks assigned by admin to teachers"""
    try:
        # Get all admin-created assignments
        tasks = list(assignments_collection.find({"createdBy": "admin"}))
        admin_tasks = []
        for t in tasks:
            admin_tasks.append({
                "id": str(t["_id"]),
                "title": t["title"],
                "description": t["description"],
                "status": t.get("status", "Pending"),
                "dueDate": t.get("dueDate"),
                "teacherId": str(t.get("teacherId", ""))
            })
        return jsonify(admin_tasks), 200
    except Exception as e:
        print(f"Error fetching admin tasks: {e}")
        return jsonify({"error": "Failed to fetch admin tasks"}), 500

@teacher_bp.route('/admin-assignments/<assignment_id>/complete', methods=['PATCH'])
def mark_assignment_complete(assignment_id):
    try:
        result = assignments_collection.update_one(
            {"_id": ObjectId(assignment_id)},
            {"$set": {"status": "Completed"}}
        )
        if result.modified_count == 1:
            return jsonify({"success": True}), 200
        return jsonify({"error": "Assignment not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NEW: Edit Assignment Route ---
@teacher_bp.route('/assignments/<assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """Update an existing assignment"""
    try:
        data = request.get_json()
        
        update_fields = {}
        if 'title' in data:
            update_fields['title'] = data['title']
        if 'description' in data:
            update_fields['description'] = data['description']
        if 'dueDate' in data:
            update_fields['dueDate'] = data['dueDate']
            
        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400
        
        # Update in MongoDB
        result = teacher_assignments_collection.update_one(
            {"_id": ObjectId(assignment_id)},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Assignment not found"}), 404
            
        # Get the updated assignment
        updated_assignment = teacher_assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        assignment_dict = {
            "id": str(updated_assignment["_id"]),
            "title": updated_assignment["title"],
            "description": updated_assignment["description"],
            "dueDate": updated_assignment["dueDate"],
            "type": updated_assignment.get("type", "manual"),
            "createdBy": updated_assignment["createdBy"]
        }
            
        return jsonify({"message": "Assignment updated successfully", "assignment": assignment_dict}), 200
        
    except Exception as e:
        print(f"Error updating assignment: {e}")
        return jsonify({"error": "Failed to update assignment"}), 500

@teacher_bp.route('/submissions', methods=['GET'])
def get_all_submissions():
    """Get all student submissions organized by student"""
    try:
        # Get all students
        students = list(users_collection.find({"role": "student"}))
        
        # Get all teacher assignments
        assignments = list(teacher_assignments_collection.find({"createdBy": "teacher"}))
        
        # Get all submissions
        submissions = list(submissions_collection.find())
        
        # Create a lookup for submissions by student_id and assignment_id
        submission_lookup = {}
        for sub in submissions:
            key = f"{sub['student_id']}_{sub['assignment_id']}"
            submission_data = {
                "id": str(sub["_id"]),
                "filename": sub["filename"],
                "file_path": sub["file_path"],
                "notes": sub.get("notes", ""),
                "submitted_at": sub["submitted_at"].isoformat()
            }
            
            # Include quiz score if available
            if "quiz_score" in sub:
                submission_data["quiz_score"] = sub["quiz_score"]
            
            submission_lookup[key] = submission_data
        
        # Build student data with assignment statuses
        student_submissions = []
        for student in students:
            student_id = str(student["_id"])
            student_data = {
                "student_id": student_id,
                "student_name": student["name"],
                "student_email": student.get("email", ""),
                "assignments": []
            }
            
            # Check each assignment for this student
            for assignment in assignments:
                assignment_id = str(assignment["_id"])
                submission_key = f"{student_id}_{assignment_id}"
                
                assignment_status = {
                    "assignment_id": assignment_id,
                    "assignment_title": assignment["title"],
                    "assignment_type": assignment.get("type", "Assignment"),
                    "due_date": assignment.get("dueDate", ""),
                    "submitted": submission_key in submission_lookup,
                    "submission": submission_lookup.get(submission_key)
                }
                
                student_data["assignments"].append(assignment_status)
            
            student_submissions.append(student_data)
        
        return jsonify(student_submissions), 200
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        return jsonify({"error": "Failed to fetch submissions"}), 500