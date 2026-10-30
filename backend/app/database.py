import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_LOCAL_URI = os.getenv("MONGO_LOCAL_URI", "mongodb://localhost:27017/")

client = None
db = None


class DummyCollection:
    def find(self, *args, **kwargs): return []
    def find_one(self, *args, **kwargs): return None
    def insert_one(self, *args, **kwargs): 
        class InsertResult: inserted_id = "demo_id"
        return InsertResult()
    def update_one(self, *args, **kwargs): return None
    def find_one_and_update(self, *args, **kwargs): return None
    def delete_one(self, *args, **kwargs): return None
    def count_documents(self, *args, **kwargs): return 0

class DummyDB:
    def __getattr__(self, name): return DummyCollection()
    def __getitem__(self, name): return DummyCollection()


def _print_warning_banner(reason: str):
    """Loud, unmissable banner: the app is running WITHOUT a real database."""
    banner = f"""
{'#' * 78}
#  {'!!  RUNNING IN DEMO MODE - NO REAL DATABASE  !!':^74}  #
#                                                                          #
#  Reason: {reason[:64]:<64}  #
#                                                                          #
#  Everything that needs persistence (login data, GD rounds, results,      #
#  submissions) will NOT be saved. API calls return demo placeholders      #
#  (user id "demo_id"), and GD evaluation/rounds will fail or be empty.    #
#                                                                          #
#  Fix: check your internet / whitelist this machine's public IP in        #
#  Atlas (cloud.mongodb.com -> Network Access), or start a local MongoDB   #
#  on mongodb://localhost:27017/.                                          #
{'#' * 78}
"""
    print(banner)                      # stdout: normal console runs
    print(banner, file=sys.stderr)     # stderr: error logs / redirected runs


def _print_fallback_banner(uri_target: str):
    """Softer banner: Atlas down but a local MongoDB took over."""
    banner = f"""
{'!' * 78}
!!  WARNING: MongoDB Atlas unreachable - FELL BACK TO LOCAL MongoDB  !!
!!  Now using: {uri_target[:56]:<56}  !!
!!  Data written here will NOT sync back to Atlas.                   !!
{'!' * 78}
"""
    print(banner)
    print(banner, file=sys.stderr)


if MONGO_URI:
    atlas_error = None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['lms_portal']
        print("Connected to MongoDB Atlas successfully")
    except Exception as e:
        atlas_error = str(e)
        client = None
        # --- Automatic fallback: try a local MongoDB before giving up ---
        try:
            local_client = MongoClient(MONGO_LOCAL_URI, serverSelectionTimeoutMS=3000)
            local_client.admin.command('ping')
            client = local_client
            db = client['lms_portal']
            _print_fallback_banner(MONGO_LOCAL_URI)
        except Exception:
            client = None
            db = DummyDB()
            short = atlas_error.split(',')[0].strip() or "unknown connection error"
            _print_warning_banner(short)
else:
    db = DummyDB()
    _print_warning_banner("MONGO_URI is not set in backend/.env")

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

# ---------------------------------------------------------------------------
# Placement Training Skill Card System collections
# NOTE: MongoDB is a demo-modeDummyDB fallback-safe: every guarantee below is
# also enforced transactionally in the service layer, so the feature still
# behaves correctly if index creation is skipped.
# ---------------------------------------------------------------------------
skill_topics_collection = db.skill_topics
skill_topic_assignments_collection = db.skill_topic_assignments
skill_lessons_collection = db.skill_lessons
skill_lesson_progress_collection = db.skill_lesson_progress
skill_problems_collection = db.skill_problems
skill_submissions_collection = db.skill_submissions
skill_assessments_collection = db.skill_assessments
skill_assessment_attempts_collection = db.skill_assessment_attempts
skill_xp_transactions_collection = db.skill_xp_transactions
skill_badge_rules_collection = db.skill_badge_rules
skill_badge_awards_collection = db.skill_badge_awards
skill_activity_history_collection = db.skill_activity_history
skill_settings_collection = db.skill_settings
skill_audit_log_collection = db.skill_audit_log


def ensure_skill_indexes():
    """Idempotent indexes enforcing the duplicate-prevention guarantees.

    - One solved-count credit per (student, problem).
    - One lesson completion per (student, lesson).
    - One XP award per dedup key: double-clicks and concurrent request
      races can never create duplicate completion rewards.
    - One progress badge award per (student, topic, badge).
    """
    from pymongo import ASCENDING

    skill_lesson_progress_collection.create_index(
        [("student_id", ASCENDING), ("lesson_id", ASCENDING)],
        name="uniq_student_lesson", unique=True)
    skill_submissions_collection.create_index(
        [("student_id", ASCENDING), ("problem_id", ASCENDING), ("solved_credit", ASCENDING)],
        name="uniq_student_problem", unique=True,
        partialFilterExpression={"solved_credit": True})
    skill_xp_transactions_collection.create_index(
        [("award_key", ASCENDING)], name="uniq_award_key", unique=True)
    skill_badge_awards_collection.create_index(
        [("student_id", ASCENDING), ("topic_id", ASCENDING), ("badge_key", ASCENDING)],
        name="uniq_student_topic_badge", unique=True)
    skill_assessment_attempts_collection.create_index(
        [("student_id", ASCENDING), ("assessment_id", ASCENDING), ("attempt_no", ASCENDING)],
        name="uniq_student_attempt", unique=True)
    skill_topic_assignments_collection.create_index(
        [("topic_id", ASCENDING), ("student_id", ASCENDING)],
        name="uniq_topic_student", unique=True, sparse=True)
    skill_activity_history_collection.create_index(
        [("student_id", ASCENDING), ("at", ASCENDING)], name="student_activity_time")
    skill_submissions_collection.create_index(
        [("problem_id", ASCENDING), ("at", ASCENDING)], name="problem_submissions_time")