# lms_portal_backend/app/database.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Ensure the MONGO_URI is set
if not MONGO_URI:
    raise ValueError("No MONGO_URI found in environment variables. Please create a .env file.")

try:
    # Initialize the MongoDB client
    client = MongoClient(MONGO_URI)
    
    # Get the database instance
    db = client['lms_portal']
    
    # Test the connection
    client.admin.command('ping')
    print("Connected to MongoDB Atlas successfully")
    
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    raise

# Create collections
users_collection = db.users
assignments_collection = db.assignments
submissions_collection = db.submissions
teacher_assignments_collection = db.teacher_assignments  # For teacher-created assignments

# GD (Group Discussion) collections
gd_rounds_collection = db.gd_rounds  # Stores scheduled GD rounds
gd_results_collection = db.gd_results  # Stores GD results and evaluations
gd_notifications_collection = db.gd_notifications  # Stores GD notifications for students