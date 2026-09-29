# test_assignments_regression.py
"""Regression test: the student assignments endpoints must not crash when a
teacher assignment document is missing fields (dueDate / title / description).

Background: `get_student_assignments_by_id` used hard key access
(`a["dueDate"]`), so ONE legacy assignment without a `dueDate` made the whole
endpoint return HTTP 500 - students then saw "No assignments available" and
could not start any quiz or Mock-Interview-adjacent work.

These tests exercise the REAL route functions with a stubbed
teacher_assignments_collection (same stubbing approach as
run_assessment_tests.py), so no MongoDB server is required.

Run:  cd backend && ../.venv/Scripts/python.exe test_assignments_regression.py
"""
import sys
import os
import types
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub MongoDB BEFORE importing any app modules (database.py connects at
# import time against Atlas).
import pymongo


class StubFindResult:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, *a, **k):
        return self

    def __iter__(self):
        return iter(self._docs)

    def __next__(self):
        return next(iter(self._docs))

    def __getattr__(self, name):
        return lambda *a, **k: self


class StubCollection:
    """Minimal pymongo collection emulation sufficient for the routes."""

    def __init__(self):
        self.docs = {}
        self._next_id = 1

    def _match(self, query, doc):
        for key, expected in (query or {}).items():
            if key == '_id':
                if doc.get('_id') != expected:
                    return False
            elif isinstance(expected, dict):
                val = doc.get(key)
                if '$ne' in expected and val == expected['$ne']:
                    return False
                if '$exists' in expected:
                    exists = key in doc
                    if expected['$exists'] and not exists:
                        return False
                    if not expected['$exists'] and exists:
                        return False
                if '$in' in expected and val not in expected['$in']:
                    return False
            elif isinstance(expected, list):
                if doc.get(key) != expected:
                    return False
            else:
                if doc.get(key) != expected:
                    return False
        return True

    def find_one(self, query=None, *a, **k):
        query = query or {}
        for doc in self.docs.values():
            if self._match(query, doc):
                return dict(doc)
        return None

    def find(self, query=None, *a, **k):
        query = query or {}
        return StubFindResult([dict(d) for d in self.docs.values() if self._match(query, d)])

    def insert_one(self, doc):
        _id = doc.get('_id', self._next_id)
        self._next_id += 1
        stored = dict(doc)
        stored['_id'] = _id
        self.docs[_id] = stored

        class R:
            inserted_id = _id

        return R()

    def update_one(self, query, update, *a, **k):
        class R:
            matched_count = 0
            modified_count = 0

        for _id, doc in list(self.docs.items()):
            if self._match(query, doc):
                R.matched_count += 1
                self._apply(doc, update)
                R.modified_count += 1
        return R()

    def _apply(self, doc, update):
        for op, fields in update.items():
            if op == '$set':
                for k, v in fields.items():
                    doc[k] = v
            elif op == '$push':
                for k, v in fields.items():
                    doc.setdefault(k, []).append(v)
            elif op == '$pull':
                for k, cond in fields.items():
                    if isinstance(cond, dict) and k in doc:
                        doc[k] = [x for x in doc[k] if not all(
                            doc_k == doc.get(doc_k) or doc_k != doc_k
                            for doc_k in [])] if False else doc[k]

    def count_documents(self, query=None, *a, **k):
        query = query or {}
        return sum(1 for d in self.docs.values() if self._match(query, d))

    def create_index(self, *a, **k):
        pass

    def delete_many(self, *a, **k):
        self.docs.clear()


def _install_stubs():
    import backend.app.database as database

    teacher_col = StubCollection()
    database.teacher_assignments_collection = teacher_col
    database.assignments_collection = StubCollection()
    database.submissions_collection = StubCollection()
    database.users_collection = StubCollection()
    return teacher_col


TEACHER_ASSIGNMENTS = _install_stubs()

# Controllable "last login" reference used by the isNew computation.
import backend.app.routes.student_routes as student_routes

student_routes.get_last_login_time = lambda: datetime(2020, 1, 1)

import unittest


class TestAssignmentsMissingFields(unittest.TestCase):
    def setUp(self):
        TEACHER_ASSIGNMENTS.docs.clear()

    def _seed_assignments(self):
        """One WELL-FORMED quiz assignment + one legacy doc missing
        dueDate/title/description (the shape that used to 500 the endpoint)."""
        from bson import ObjectId

        good_id = ObjectId()
        TEACHER_ASSIGNMENTS.docs[good_id] = {
            '_id': good_id,
            'title': 'Good Quiz',
            'description': 'well formed',
            'dueDate': '2026-12-31',
            'type': 'Quiz',
            'createdBy': 'teacher',
            'quizQuestions': [
                {'question': '2+2?', 'options': ['3', '4'], 'correct_answer': '4'},
            ],
        }
        bad_id = ObjectId()
        TEACHER_ASSIGNMENTS.docs[bad_id] = {
            '_id': bad_id,
            'createdBy': 'teacher',
            # NO title, NO description, NO dueDate, NO type
        }
        return str(good_id), str(bad_id)

    def test_by_id_endpoint_200_with_missing_fields(self):
        """The exact regression: a doc without dueDate must not 500 the list."""
        app = student_routes.student_bp  # blueprint carries the route funcs

        from flask import Flask
        flask_app = Flask(__name__)
        flask_app.register_blueprint(app)

        good_id, bad_id = self._seed_assignments()
        client = flask_app.test_client()

        resp = client.get(f'/api/student/some_student/assignments')
        self.assertEqual(resp.status_code, 200,
                         f"expected 200, got {resp.status_code}: {resp.get_json()}")
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        by_id = {a['id']: a for a in data}
        # Missing fields are filled with safe defaults, never KeyError.
        self.assertEqual(by_id[bad_id]['title'], 'Untitled')
        self.assertEqual(by_id[bad_id]['description'], '')
        self.assertIsNone(by_id[bad_id]['dueDate'])
        self.assertEqual(by_id[bad_id]['type'], 'manual')
        # The well-formed quiz keeps its data and quiz_questions.
        self.assertEqual(by_id[good_id]['title'], 'Good Quiz')
        self.assertEqual(by_id[good_id]['type'], 'Quiz')
        self.assertEqual(len(by_id[good_id]['quiz_questions']), 1)

    def test_general_endpoint_200_with_missing_fields(self):
        from flask import Flask
        flask_app = Flask(__name__)
        flask_app.register_blueprint(student_routes.student_bp)

        good_id, bad_id = self._seed_assignments()
        client = flask_app.test_client()

        resp = client.get('/api/student/assignments')
        self.assertEqual(resp.status_code, 200,
                         f"expected 200, got {resp.status_code}: {resp.get_json()}")
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        bad = next(a for a in data if a['id'] == bad_id)
        self.assertEqual(bad['title'], 'Untitled')
        self.assertIsNone(bad['dueDate'])

    def test_completely_empty_assignment_doc(self):
        """Even a doc with ONLY _id survives (no title/desc/dueDate/type)."""
        from bson import ObjectId
        from flask import Flask
        flask_app = Flask(__name__)
        flask_app.register_blueprint(student_routes.student_bp)

        bare_id = ObjectId()
        TEACHER_ASSIGNMENTS.docs[bare_id] = {'_id': bare_id, 'createdBy': 'teacher'}
        client = flask_app.test_client()

        resp = client.get('/api/student/some_student/assignments')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Untitled')
        self.assertEqual(data[0]['type'], 'manual')


if __name__ == '__main__':
    unittest.main(verbosity=2)
