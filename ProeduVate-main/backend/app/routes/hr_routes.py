# lms_portal_backend/app/routes/hr_routes.py

from flask import Blueprint, jsonify
from ..database import users_collection, submissions_collection
from ..models.user import user_helper

hr_bp = Blueprint('hr_bp', __name__, url_prefix='/api/hr')

@hr_bp.route('/candidates', methods=['GET'])
def get_all_candidates():
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