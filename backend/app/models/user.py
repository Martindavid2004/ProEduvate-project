# lms_portal_backend/app/models/user.py

from bson import ObjectId
import random

def user_helper(user, submissions_count=None) -> dict:
    user_data = {
        "id": str(user["_id"]),
        "name": user["name"],
        "role": user["role"],
        "department": user.get("department", ""),
        "idNumber": user.get("idNumber", ""),
        "subject": user.get("subject"),
        "rollNo": user.get("rollNo"),
        "companyName": user.get("companyName"),
        "jobRoles": user.get("jobRoles"),
        "email": user.get("email", ""),
        "attendance": user.get("attendance", 0),
        "average_score": user.get("average_score", 0),
        "interviewScore": user.get("interviewScore"),
        "resumeScore": user.get("resumeScore"),
        "atsScore": user.get("atsScore"),
        "resume_filename": user.get("resume_filename"),
        "matchingSkills": user.get("matchingSkills", []),
        "missingSkills": user.get("missingSkills", []),
        "resumeSummary": user.get("resumeSummary", ""),
        "trainingScore": user.get("trainingScore"),
        "submittedAssignments": user.get("submittedAssignments", 0)
    }
    
    # Override with actual count if provided
    if submissions_count is not None:
        user_data["submittedAssignments"] = submissions_count
    
    return user_data

def generate_student_scores():
    return {
        "atsScore": random.randint(60, 95),
        "interviewScore": random.randint(60, 95)
    }