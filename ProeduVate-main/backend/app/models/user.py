# lms_portal_backend/app/models/user.py

from bson import ObjectId
import random

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "role": user["role"],
        "atsScore": user.get("atsScore"),
        "interviewScore": user.get("interviewScore"),
        "resume_filename": user.get("resume_filename") # NEW: Add this line
    }

def generate_student_scores():
    return {
        "atsScore": random.randint(60, 95),
        "interviewScore": random.randint(60, 95)
    }