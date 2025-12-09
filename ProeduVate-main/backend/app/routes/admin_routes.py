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
        "role": data['role']
    }
    # Add random scores if the user is a student
    if data['role'] == 'student':
        new_user.update(generate_student_scores())

    result = users_collection.insert_one(new_user)
    created_user = users_collection.find_one({"_id": result.inserted_id})
    return jsonify(user_helper(created_user)), 201

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    all_users = [user_helper(user) for user in users_collection.find()]
    return jsonify(all_users)

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return jsonify({"success": True, "message": "User deleted"}), 200
    return jsonify({"error": "User not found"}), 404

# --- Assignment Management ---
@admin_bp.route('/assignments', methods=['POST'])
def assign_work():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('teacherId') or not data.get('description'):
        return jsonify({"error": "Missing required assignment fields"}), 400

    new_assignment = {
        "title": data['title'],
        "description": data['description'],
        "teacherId": ObjectId(data['teacherId']),
        "createdBy": "admin",
        "dueDate": (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
    }
    assignments_collection.insert_one(new_assignment)
    return jsonify({"success": True, "message": "Work assigned successfully"}), 201