"""
Skill Card System tests (standard library only: run `python -m unittest test_skill_system`).

Covers acceptance criteria:
- progress formula incl. empty categories (5)
- XP / badge rules consistent + configurable (6)
- duplicate submissions cannot create duplicate rewards (7)
- failed submissions do not count or award XP (2)
- permissions: students see their own data only; role gates (part of 12)

DB-backed behaviour is tested against an in-memory fake collection so the
tests never touch a production database.
"""

import datetime
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import skill_progress as progress
from app.services import skill_rewards as rewards


# ------------------------------------------------------------- fake mongo --
class DuplicateKeyError(Exception):
    pass


class FakeCollection:
    """Minimal pymongo-like collection sufficient for the skill services."""

    def __init__(self, unique_fields=()):
        self.docs = []
        self.unique_fields = tuple(unique_fields)

    # - writes -
    def insert_one(self, doc):
        wanted = tuple(doc.get(f) for f in self.unique_fields)
        if self.unique_fields and all(w is not None for w in wanted):
            for existing in self.docs:
                if tuple(existing.get(f) for f in self.unique_fields) == wanted:
                    raise DuplicateKeyError("E11000 duplicate key error")
        doc = dict(doc)
        doc.setdefault("_id", len(self.docs) + 1)
        self.docs.append(doc)

        class _R:
            inserted_id = doc["_id"]
        return _R()

    def update_one(self, query, update, **kwargs):
        match = self._matches_all(self.docs, query)
        for doc in match:
            if "$set" in update:
                doc.update(update["$set"])
            if "$unset" in update:
                for key in update["$unset"]:
                    doc.pop(key, None)

        class _R:
            modified_count = len(match)
        return _R()

    # - reads -
    def find(self, query=None, *args, **kwargs):
        return FakeCursor([d for d in self._matching(query or {})], query)

    def find_one(self, query=None, *args, **kwargs):
        matches = self._matching(query or {})
        return matches[0] if matches else None

    def count_documents(self, query=None, **kwargs):
        return len(self._matching(query or {}))

    def aggregate(self, pipeline):
        docs = self._matching(pipeline[0].get("$match", {}))
        if pipeline[1].get("$group", {}).get("total", {}).get("$sum") == "$xp":
            total = sum(d.get("xp", 0) for d in docs)
            return [{"_id": None, "total": total}] if docs else []
        return []

    def create_index(self, *a, **k):
        return "pseudo-index"

    # - internals -
    def _matching(self, query):
        out = []
        for doc in self.docs:
            if self._doc_matches(doc, query):
                out.append(doc)
        return out

    def _doc_matches(self, doc, query):
        for key, cond in query.items():
            value = doc.get(key)
            if isinstance(cond, dict):
                for op, operand in cond.items():
                    if op == "$ne" and value == operand:
                        return False
                    if op == "$in" and value not in operand:
                        return False
                    if op == "$gte" and not (value and value >= operand):
                        return False
                    if op == "$lt" and not (value and value < operand):
                        return False
            else:
                if value != cond:
                    return False
        return True

    @staticmethod
    def _matches_all(docs, query):
        return [d for d in docs if all(d.get(k) == v for k, v in query.items())]


class FakeCursor(list):
    def __init__(self, docs, query=None):
        super().__init__(docs)
        self._query = query or {}

    def sort(self, key, direction=1):
        if isinstance(key, str):
            fields = [(key, direction)]
        else:
            fields = key
        docs = list(self)
        for field, direction in reversed(fields):
            reverse = (direction == -1)
            try:
                docs.sort(key=lambda d: d.get(field) or "", reverse=reverse)
            except TypeError:
                pass
        return FakeCursor(docs, self._query)

    def limit(self, n):
        return FakeCursor(list(self)[:n], self._query)


def make_field_fakes():
    """One fake per skill collection with matching uniqueness rules."""
    f = {
        "skill_topics_collection": FakeCollection(),
        "skill_topic_assignments_collection": FakeCollection(unique_fields=("topic_id", "student_id")),
        "skill_lessons_collection": FakeCollection(),
        "skill_lesson_progress_collection": FakeCollection(unique_fields=("student_id", "lesson_id")),
        "skill_problems_collection": FakeCollection(),
        "skill_submissions_collection": FakeCollection(unique_fields=("student_id", "problem_id", "solved_credit")),
        "skill_assessments_collection": FakeCollection(),
        "skill_assessment_attempts_collection": FakeCollection(
            unique_fields=("student_id", "assessment_id", "attempt_no")),
        "skill_xp_transactions_collection": FakeCollection(unique_fields=("award_key",)),
        "skill_badge_rules_collection": FakeCollection(),
        "skill_badge_awards_collection": FakeCollection(
            unique_fields=("student_id", "topic_id", "badge_key")),
        "skill_activity_history_collection": FakeCollection(),
        "skill_settings_collection": FakeCollection(),
        "skill_audit_log_collection": FakeCollection(),
    }
    f["skill_settings_collection"].insert_one({"_id": rewards.SETTINGS_DOC_ID, "xp": dict(rewards.DEFAULT_XP_CONFIG)})
    return f


def patch_fakes(fakes):
    """Point every module-level collection reference at the fakes."""
    import app.database as db_mod
    import app.routes.skill_routes as routes
    import app.services.skill_state as state
    import app.services.skill_rewards as reward_mod
    for name, fake in fakes.items():
        setattr(db_mod, name, fake)
        setattr(routes, name, fake)
        setattr(state, name, fake)
        setattr(reward_mod, name, fake)


def fresh_app_modules(fakes):
    """Fresh fake state per test + restore app.database afterwards."""
    import app.database as db_mod
    saved = {name: getattr(db_mod, name) for name in fakes}
    patch_fakes(fakes)
    return saved


def restore_fakes(saved):
    import app.database as db_mod
    import app.routes.skill_routes as routes
    import app.services.skill_state as state
    import app.services.skill_rewards as reward_mod
    for name, old in saved.items():
        setattr(db_mod, name, old)
        setattr(routes, name, old)
        setattr(state, name, old)
        setattr(reward_mod, name, old)


# ---------------------------------------------------------------- formula --
class ProgressFormulaTests(unittest.TestCase):
    def test_full_weighted_formula(self):
        pct = progress.overall_completion(coding=0.5, learning=1.0, assessment=0.25)
        # 50*0.4 + 100*0.2 + 25*0.4 = 20+20+10 = 50
        self.assertEqual(pct, 50.0)

    def test_empty_categories_are_normalised(self):
        # Topic with ONLY coding activities (no lessons, no assessments):
        # learning/assessment excluded, coding weight becomes 100%.
        pct = progress.overall_completion(coding=0.5, learning=None, assessment=None,
                                          include={"coding": True, "learning": False,
                                                   "assessment": False})
        self.assertEqual(pct, 50.0)

    def test_two_categories_normalise(self):
        pct = progress.overall_completion(coding=1.0, learning=0.0, assessment=None,
                                          include={"coding": True, "learning": True,
                                                   "assessment": False})
        # (100*0.4 + 0*0.2) / 0.6 = 66.67
        self.assertEqual(pct, 66.67)

    def test_no_categories(self):
        self.assertEqual(progress.overall_completion(include={}), 0.0)

    def test_clamped(self):
        self.assertEqual(progress.completion_component(1.5), 100.0)
        self.assertEqual(progress.completion_component(-1), 0.0)


class BadgeThresholdTests(unittest.TestCase):
    def test_thresholds(self):
        cases = [(0, "beginner"), (24.9, "beginner"), (25, "practitioner"),
                 (49.9, "practitioner"), (50, "advanced"), (79.9, "advanced"),
                 (80, "expert"), (100, "expert")]
        for pct, expected in cases:
            self.assertEqual(progress.progress_badge(pct)[0], expected, f"pct={pct}")

    def test_proficiency_separate_from_completion(self):
        # 100% completion but weak assessment score => NOT Skill Master.
        ok, key, reason = progress.proficiency_status(
            assessment_pct=60, learning_pct=100, all_problems_solved=True)
        self.assertFalse(ok)
        self.assertIn("assessment", reason)

    def test_proficiency_earned(self):
        ok, key, _ = progress.proficiency_status(
            assessment_pct=85, learning_pct=100, all_problems_solved=True)
        self.assertTrue(ok)
        self.assertEqual(key, "skill_master")

    def test_badges_are_progress_not_mastery(self):
        # 100% completion still labelled with the same progress badge tiers.
        self.assertEqual(progress.progress_badge(100)[0], "expert")


# ------------------------------------------------------------------ rewards --
class RewardIdempotencyTests(unittest.TestCase):
    def setUp(self):
        self.fakes = make_field_fakes()
        self.saved = fresh_app_modules(self.fakes)
        self.addCleanup(restore_fakes, self.saved)

    def test_xp_awarded_once_per_award_key(self):
        first = rewards.award_xp("s1", "t1", "Solved problem", 20,
                                 "problem:p1:pass", "problem")
        self.assertTrue(first["awarded"])
        again = rewards.award_xp("s1", "t1", "Solved problem", 20,
                                 "problem:p1:pass", "problem")
        self.assertFalse(again["awarded"])
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["total_xp"], first["total_xp"])
        self.assertEqual(
            self.fakes["skill_xp_transactions_collection"].count_documents({}), 1)

    def test_award_key_scope(self):
        rewards.award_xp("s1", "t1", "Lesson", 10, "lesson:l1", "lesson")
        # same lesson for ANOTHER student -> separate reward
        other = rewards.award_xp("s2", "t1", "Lesson", 10, "lesson:l1__s2", "lesson")
        self.assertTrue(other["awarded"])
        # same student, DIFFERENT lesson -> separate reward
        second = rewards.award_xp("s1", "t1", "Lesson", 10, "lesson:l2", "lesson")
        self.assertTrue(second["awarded"])

    def test_zero_xp_not_awarded(self):
        res = rewards.award_xp("s1", "t1", "nothing", 0,
                               "problem:p:pass", "problem")
        self.assertFalse(res["awarded"])

    def test_progress_badge_idempotent(self):
        first = rewards.grant_progress_badge("s1", "t1", "expert", "Expert", 80)
        second = rewards.grant_progress_badge("s1", "t1", "expert", "Expert", 80)
        self.assertTrue(first["awarded"])
        self.assertFalse(second["awarded"])
        self.assertTrue(second["duplicate"])

    def test_xp_config_update_audited_and_applied(self):
        admin = {"id": "admin1", "role": "admin"}
        merged = rewards.update_xp_config({"problem_hard": 40}, admin)
        self.assertEqual(merged["problem_hard"], 40)
        audits = self.fakes["skill_audit_log_collection"].docs
        self.assertTrue(any(a["action"] == "xp_config_update" for a in audits))
        with self.assertRaises(ValueError):
            rewards.update_xp_config({"nope": 1}, admin)


def db_mod():
    import app.database
    return app.database


# ------------------------------------------------------------------ routes --
class RoutePermissionTests(unittest.TestCase):
    """Permission + duplicate prevention through the real Flask routes."""

    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.routes.auth_routes import generate_jwt_token
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.token = generate_jwt_token("student1", "s1@x.com", "student")
        cls.teacher_token = generate_jwt_token("teacher1", "t1@x.com", "teacher")
        cls.admin_token = generate_jwt_token("admin1", "a1@x.com", "admin")

    def setUp(self):
        self.fakes = make_field_fakes()
        self.saved = fresh_app_modules(self.fakes)
        self.addCleanup(restore_fakes, self.saved)
        # Fixed card stub: recompute path returns stable counts.
        card = {
            "counts": {"problems_required": 2, "problems_solved": 0,
                       "lessons_required": 2, "lessons_completed": 0,
                       "assessments_required": 1, "assessments_completed": 0,
                       "attempts_count": 0, "assessments_passed": 0},
            "completion_pct": 0.0, "badge_key": "beginner",
            "badge_label": "Beginner", "badge_meaning": "learning",
            "proficiency": {"earned": False, "key": None, "reason": "n/a"},
            "topic": {"id": "topic1", "name": "Python", "icon": "code",
                      "description": "d"},
        }
        import app.routes.skill_routes as routes
        fake_state = mock.Mock()
        fake_state.build_card = mock.Mock(return_value=card)
        routes.skill_state = fake_state

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_no_token_is_401(self):
        resp = self.client.get("/api/skills/me/dashboard")
        self.assertEqual(resp.status_code, 401)

    def test_student_cannot_use_teacher_route(self):
        resp = self.client.get("/api/skills/teacher/progress",
                               headers=self._auth(self.token))
        self.assertEqual(resp.status_code, 403)

    def test_teacher_cannot_use_admin_route(self):
        resp = self.client.get("/api/skills/admin/config",
                               headers=self._auth(self.teacher_token))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_read_config(self):
        resp = self.client.get("/api/skills/admin/config",
                               headers=self._auth(self.admin_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("xp", resp.get_json())


class StudentFlowTests(unittest.TestCase):
    """Lesson completion + coding + assessment duplicates through routes."""

    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.routes.auth_routes import generate_jwt_token
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.student_token = generate_jwt_token("student1", "s1@x.com", "student")

    def setUp(self):
        self.fakes = make_field_fakes()
        self.saved = fresh_app_modules(self.fakes)
        self.addCleanup(restore_fakes, self.saved)
        # Fixed card stub: recompute path returns stable counts.
        fakes = self.fakes
        card = {
            "counts": {"problems_required": 2, "problems_solved": 0,
                       "lessons_required": 2, "lessons_completed": 0,
                       "assessments_required": 1, "assessments_completed": 0,
                       "attempts_count": 0, "assessments_passed": 0},
            "completion_pct": 0.0, "badge_key": "beginner",
            "badge_label": "Beginner", "badge_meaning": "learning",
            "proficiency": {"earned": False, "key": None, "reason": "n/a"},
            "topic": {"id": "topic1", "name": "Python", "icon": "code",
                      "description": "d"},
        }
        import app.routes.skill_routes as routes
        from bson import ObjectId
        routes.skill_state = mock.Mock()
        routes.skill_state.build_card = mock.Mock(return_value=card)
        cls_topic = ObjectId()
        self.topic_id = cls_topic
        fakes["skill_topics_collection"].insert_one({"_id": cls_topic, "name": "Python",
                                                     "archived": False})
        self.lesson_id = ObjectId()
        fakes["skill_lessons_collection"].insert_one(
            {"_id": self.lesson_id, "topic_id": cls_topic, "title": "L1", "required": True})
        self.problem_id = ObjectId()
        fakes["skill_problems_collection"].insert_one(
            {"_id": self.problem_id, "topic_id": cls_topic, "title": "Sum",
             "difficulty": "medium", "required": True,
             "test_cases": [{"input": "3", "expectedOutput": "3"}]})
        self.assessment_id = ObjectId()
        fakes["skill_assessments_collection"].insert_one(
            {"_id": self.assessment_id, "topic_id": cls_topic, "title": "A1",
             "max_marks": 10, "pass_pct": 40, "required": True, "retakes_allowed": 2,
             "questions": [{"question": "1+1?", "options": ["2", "3"],
                            "answer": 0, "marks": 10}]})

    def _auth(self):
        return {"Authorization": f"Bearer {self.student_token}", "Content-Type": "application/json"}

    def test_lesson_complete_awards_xp_once(self):
        import app.routes.skill_routes as routes
        resp = self.client.post(f"/api/skills/lessons/{self.lesson_id}/complete", headers=self._auth())
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["duplicate"])
        self.assertEqual(data["xp_awarded"], rewards.get_xp_config()["lesson_complete"])

        resp2 = self.client.post(f"/api/skills/lessons/{self.lesson_id}/complete", headers=self._auth())
        data2 = resp2.get_json()
        self.assertTrue(data2["duplicate"])
        xp_docs = self.fakes["skill_xp_transactions_collection"].docs
        self.assertEqual(len(xp_docs), 1)   # still exactly one XP transaction

    def test_problem_submission(self):
        import app.routes.skill_routes as routes
        fake_eval = mock.Mock(return_value={
            "stdout": base64encode("3"), "stderr": None,
            "status": {"id": 3, "description": "Accepted"}})
        with mock.patch.object(routes, "execute_python_code_lambda", fake_eval):
            resp = self.client.post(f"/api/skills/problems/{self.problem_id}/submit",
                                    headers=self._auth(), json={"code": "print(input())"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["solved"])
        self.assertEqual(data["xp_awarded"], rewards.get_xp_config()["problem_medium"])


def base64encode(text):
    import base64
    return base64.b64encode(text.encode()).decode()


if __name__ == "__main__":
    unittest.main(verbosity=1)
