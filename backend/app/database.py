import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None

class DummyCollection:
    def find(self, *args, **kwargs): return []
    def find_one(self, *args, **kwargs): return None
    def insert_one(self, *args, **kwargs): 
        class InsertResult: inserted_id = "demo_id"
        return InsertResult()
    def update_one(self, *args, **kwargs): return None
    def delete_one(self, *args, **kwargs): return None
    def count_documents(self, *args, **kwargs): return 0

class DummyDB:
    def __getattr__(self, name): return DummyCollection()
    def __getitem__(self, name): return DummyCollection()

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['lms_portal']
        client.admin.command('ping')
        print("Connected to MongoDB Atlas successfully")
    except Exception as e:
        print(f"MongoDB connection warning: {e}")
        db = DummyDB()
else:
    db = DummyDB()

users_collection = db.users
assignments_collection = db.assignments
submissions_collection = db.submissions
teacher_assignments_collection = db.teacher_assignments
gd_rounds_collection = db.gd_rounds
gd_results_collection = db.gd_results
gd_notifications_collection = db.gd_notifications
aptitude_concepts_collection = db.aptitude_concepts
aptitude_practice_collection = db.aptitude_practice
aptitude_test_questions_collection = db.aptitude_test_questions