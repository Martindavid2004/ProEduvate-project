# lms_portal_backend/app/routes/admin_routes.py

from flask import Blueprint, request, jsonify
from ..database import users_collection, assignments_collection
from ..models.user import user_helper, generate_student_scores
from bson import ObjectId
import datetime

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/api/admin')

# --- User Management ---
@admin_bp.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('role'):
        return jsonify({"error": "Missing name or role"}), 400

    new_user = {
        "name": data['name'],
        "role": data['role'],
        "department": data.get('department', ''),
        "idNumber": data.get('idNumber', '')
    }
    
    # Add role-specific fields
    if data['role'] == 'teacher' and data.get('subject'):
        new_user['subject'] = data['subject']
    elif data['role'] == 'student':
        if data.get('rollNo'):
            new_user['rollNo'] = data['rollNo']
        # Add random scores if the user is a student
        new_user.update(generate_student_scores())
    elif data['role'] == 'hr':
        if data.get('companyName'):
            new_user['companyName'] = data['companyName']
        if data.get('jobRoles'):
            new_user['jobRoles'] = data['jobRoles']

    result = users_collection.insert_one(new_user)
    created_user = users_collection.find_one({"_id": result.inserted_id})
    return jsonify(user_helper(created_user)), 201

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    from ..database import submissions_collection
    
    all_users = []
    for user in users_collection.find():
        if user.get('role') == 'student':
            student_id = str(user["_id"])
            # Get submission count for this student
            submission_count = submissions_collection.count_documents({"student_id": student_id})
            
            # Update student record with submission count
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"submittedAssignments": submission_count}}
            )
            
            all_users.append(user_helper(user, submission_count))
        else:
            all_users.append(user_helper(user))
    
    return jsonify(all_users)

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return jsonify({"success": True, "message": "User deleted"}), 200
    return jsonify({"error": "User not found"}), 404

# --- Assignment Management ---
@admin_bp.route('/assignments', methods=['GET'])
def get_assignments():
    """Get all assignments"""
    try:
        all_assignments = [
            {
                "id": str(a["_id"]),
                "title": a["title"],
                "description": a["description"],
                "teacherId": str(a.get("teacherId", "")),
                "createdBy": a.get("createdBy", "admin"),
                "dueDate": a.get("dueDate")
            }
            for a in assignments_collection.find()
        ]
        return jsonify(all_assignments), 200
    except Exception as e:
        print(f"Error fetching assignments: {e}")
        return jsonify({"error": "Failed to fetch assignments"}), 500

@admin_bp.route('/assignments', methods=['POST'])
def assign_work():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('teacherId') or not data.get('description'):
        return jsonify({"error": "Missing required assignment fields"}), 400

    new_assignment = {
        "title": data['title'],
        "description": data['description'],
        "teacherId": ObjectId(data['teacherId']),
        "createdBy": data.get("createdBy", "admin"),
        "status": data.get("status", "pending"),
        "dueDate": (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    }
    result = assignments_collection.insert_one(new_assignment)
    
    # Return the created assignment with its ID
    created_assignment = {
        "id": str(result.inserted_id),
        "title": new_assignment["title"],
        "description": new_assignment["description"],
        "teacherId": str(new_assignment["teacherId"]),
        "createdBy": new_assignment["createdBy"],
        "status": new_assignment["status"],
        "dueDate": new_assignment["dueDate"]
    }
    
    return jsonify({"success": True, "message": "Work assigned successfully", "assignment": created_assignment}), 201

@admin_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get system status overview"""
    try:
        total_users = users_collection.count_documents({})
        total_students = users_collection.count_documents({"role": "student"})
        total_teachers = users_collection.count_documents({"role": "teacher"})
        total_assignments = assignments_collection.count_documents({})
        
        return jsonify({
            "totalUsers": total_users,
            "totalStudents": total_students,
            "totalTeachers": total_teachers,
            "totalAssignments": total_assignments,
            "systemHealth": "Operational"
        }), 200
    except Exception as e:
        print(f"Error fetching system status: {e}")
        return jsonify({"error": "Failed to fetch status"}), 500

@admin_bp.route('/tasks', methods=['GET'])
def get_admin_tasks():
    """Get admin tasks (assignments created by admin)"""
    try:
        # Get all assignments created by admin
        tasks = []
        for assignment in assignments_collection.find({"createdBy": "admin"}):
            # Get teacher name
            teacher = users_collection.find_one({"_id": assignment.get("teacherId")})
            teacher_name = teacher.get("name", "Unknown") if teacher else "Unknown"
            
            tasks.append({
                "id": str(assignment["_id"]),
                "title": assignment["title"],
                "description": assignment["description"],
                "teacherId": str(assignment.get("teacherId", "")),
                "teacherName": teacher_name,
                "status": assignment.get("status", "pending"),
                "createdBy": assignment.get("createdBy", "admin"),
                "dueDate": assignment.get("dueDate")
            })
        
        return jsonify(tasks), 200
    except Exception as e:
        print(f"Error fetching admin tasks: {e}")
        return jsonify({"error": "Failed to fetch tasks"}), 500

@admin_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_admin_task(task_id):
    """Update an admin task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'teacherId' in data:
            update_data['teacherId'] = ObjectId(data['teacherId'])
        if 'status' in data:
            update_data['status'] = data['status']
        
        result = assignments_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            return jsonify({"success": True, "message": "Task updated"}), 200
        elif result.matched_count == 1:
            return jsonify({"success": True, "message": "No changes made"}), 200
        else:
            return jsonify({"error": "Task not found"}), 404
            
    except Exception as e:
        print(f"Error updating task: {e}")
        return jsonify({"error": "Failed to update task"}), 500

@admin_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_admin_task(task_id):
    """Delete an admin task"""
    try:
        result = assignments_collection.delete_one({"_id": ObjectId(task_id)})
        
        if result.deleted_count == 1:
            return jsonify({"success": True, "message": "Task deleted"}), 200
        else:
            return jsonify({"error": "Task not found"}), 404
            
    except Exception as e:
        print(f"Error deleting task: {e}")
        return jsonify({"error": "Failed to delete task"}), 500