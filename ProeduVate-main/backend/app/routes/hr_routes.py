# lms_portal_backend/app/routes/hr_routes.py

from flask import Blueprint, jsonify
from ..database import users_collection
from ..models.user import user_helper

hr_bp = Blueprint('hr_bp', __name__, url_prefix='/api/hr')

@hr_bp.route('/candidates', methods=['GET'])
def get_all_candidates():
    students = users_collection.find({"role": "student"})
    student_list = [user_helper(s) for s in students]
    return jsonify(student_list)