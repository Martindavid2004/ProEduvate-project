# lms_portal_backend/app/models/assignment.py

from bson import ObjectId

# Helper to convert MongoDB's ObjectId to a string
def assignment_helper(assignment) -> dict:
    return {
        "id": str(assignment["_id"]),
        "title": assignment["title"],
        "description": assignment["description"],
        "dueDate": assignment["dueDate"],
        "teacherId": str(assignment.get("teacherId")), # Optional field
        "createdBy": assignment["createdBy"]
    }