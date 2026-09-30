# user_resolution.py
"""Shared user resolution: one source of truth for WHO the interviewee is.

Root cause this fixes: /api/interview/evaluate used to update the student's
stored interviewScore ONLY when the incoming user_id was a valid ObjectId.
Demo logins (run.py /login with username 'student') and stale frontend
sessions (localStorage 'user' with id:"student", visible in the server logs
as GET /api/student/student/progress) sent a NON-ObjectId id, the update was
silently skipped, and the Profile "Interview Score" card stayed N/A forever -
even though the session itself was evaluated and scored.

Every route that needs "the current student's user document" must go through
resolve_user() so scores, resume text and profile state always land on the
SAME record the rest of the app reads.

Demo identities are transparently mapped to a REAL users-collection document
in priority order:
  1. valid ObjectId -> that exact user
  2. email-shaped id -> users.email lookup (case-insensitive)
  3. demo username ('student', 'student@demo.com', ...) -> demo user e-mail
     -> users.email; then registerNumber / rollNo; finally the single
     role:'student' document when exactly one exists (ambiguous collections
     are NEVER guessed at).

The returned dict carries the matched Mongo _id plus how it was resolved so
callers can log/persist the right key.
"""

import os
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEMO_DOMAIN = "demo.com"


def is_object_id(value):
    try:
        from bson import ObjectId
        return bool(value) and ObjectId.is_valid(value)
    except Exception:
        return False


def demo_email_for(identifier):
    """The canonical demo e-mail for a demo username ('student' ->
    'student@demo.com'); e-mail-shaped inputs pass through unchanged."""
    ident = str(identifier or '').strip()
    if not ident:
        return None
    if _EMAIL_RE.match(ident):
        return ident.lower()
    return f"{ident.lower()}@{DEMO_DOMAIN}"


def resolve_user(user_id, users_collection=None):
    """Resolve an incoming user id (ObjectId, e-mail or demo username) to the
    real user document, or None when nothing matches.

    Returns a dict:
      { "user": <document or None>, "user_key": <ObjectId|str|None>,
        "resolved_via": <strategy label>, "is_demo": <bool> }
    """
    if users_collection is None:
        from ..database import users_collection as users_collection

    ident = str(user_id or '').strip()
    if not ident:
        return {"user": None, "user_key": None, "resolved_via": "empty_id",
                "is_demo": False}

    # 1. Real registered user: exact _id lookup.
    if is_object_id(ident):
        try:
            from bson import ObjectId
            user = users_collection.find_one({"_id": ObjectId(ident)})
            if user:
                return {"user": user, "user_key": user["_id"],
                        "resolved_via": "object_id", "is_demo": False}
        except Exception:
            pass
        return {"user": None, "user_key": None, "resolved_via": "object_id_not_found",
                "is_demo": False}

    # 2. E-mail-shaped id -> users.email.
    if _EMAIL_RE.match(ident):
        user = users_collection.find_one({
            "email": {"$regex": f"^{re.escape(ident)}$", "$options": "i"}})
        if user:
            return {"user": user, "user_key": user["_id"],
                    "resolved_via": "email", "is_demo": False}

    # 3. Demo identity: username / demo e-mail -> demo e-mail -> users.email.
    demo_email = demo_email_for(ident)
    user = users_collection.find_one({
        "email": {"$regex": f"^{re.escape(demo_email)}$", "$options": "i"}})
    if user:
        return {"user": user, "user_key": user["_id"],
                "resolved_via": "demo_email", "is_demo": True}

    # 3b. Some seeds store the demo handle directly.
    for field in ("registerNumber", "rollNo", "idNumber"):
        user = users_collection.find_one({field: ident})
        if user:
            return {"user": user, "user_key": user["_id"],
                    "resolved_via": f"field:{field}", "is_demo": True}

    # 3c. Last resort: exactly ONE student document -> use it. Ambiguous
    # (0 or 2+) collections are never guessed at.
    try:
        students = list(users_collection.find({"role": "student"}))
    except Exception:
        students = []
    if len(students) == 1:
        return {"user": students[0], "user_key": students[0]["_id"],
                "resolved_via": "single_student", "is_demo": True}

    print(f"[USER_RESOLUTION] Could not resolve user_id={ident!r} "
          f"(students_in_db={len(students)})")
    return {"user": None, "user_key": None, "resolved_via": "unresolved",
            "is_demo": _EMAIL_RE.match(ident) and ident.lower().endswith(f"@{DEMO_DOMAIN}")}


def resolve_user_key(user_id, users_collection=None):
    """Convenience: just the stable user key (ObjectId when possible)."""
    return resolve_user(user_id, users_collection)["user_key"]


def resolve_user_doc(user_id, users_collection=None):
    """Convenience: just the user document (or None)."""
    return resolve_user(user_id, users_collection)["user"]
