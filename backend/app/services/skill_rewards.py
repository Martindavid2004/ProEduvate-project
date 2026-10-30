"""
Placement Training Skill Card System - server-side reward engine.

Hard rules enforced here (never in the frontend):
- XP / completion / badge eligibility is computed ON THE SERVER.
- An award has a deterministic `award_key`; a unique index on that key makes
  duplicate submissions / double taps / concurrent races unable to create a
  second reward (returns duplicate=True instead).
- Failed attempts record analytics but award nothing.
- Every admin change to XP values or badge rules is written to the audit log.
"""

import datetime
from ..database import (
    skill_xp_transactions_collection,
    skill_badge_awards_collection,
    skill_settings_collection,
    skill_activity_history_collection,
    skill_audit_log_collection,
)

# ---------------------------------------------------------------- defaults --
DEFAULT_XP_CONFIG = {
    "lesson_complete": 10,
    "problem_easy": 10,
    "problem_medium": 20,
    "problem_hard": 30,
    "assessment_pass": 50,
    "assessment_high_score_bonus": 25,
    "topic_complete_bonus": 100,
    "high_score_threshold": 90,   # % in an assessment for the bonus
}

SETTINGS_DOC_ID = "reward_config"


def get_xp_config():
    """Configurable starting values; admins may change them via the admin API
    (persisted in skill_settings) - no code change required."""
    doc = skill_settings_collection.find_one({"_id": SETTINGS_DOC_ID})
    config = dict(DEFAULT_XP_CONFIG)
    if doc and isinstance(doc.get("xp"), dict):
        # Only known keys, cast to int, floors at 0.
        for key in DEFAULT_XP_CONFIG:
            if key in doc["xp"]:
                try:
                    config[key] = max(0, int(doc["xp"][key]))
                except (TypeError, ValueError):
                    continue
    return config


def update_xp_config(changes, actor):
    """Persist admin XP changes; records an audit-log entry."""
    if not isinstance(changes, dict) or not changes:
        raise ValueError("no changes supplied")

    current = get_xp_config()
    unknown = [k for k in changes if k not in DEFAULT_XP_CONFIG]
    if unknown:
        raise ValueError(f"unknown XP keys: {', '.join(unknown)}")

    merged = dict(current)
    for key, value in changes.items():
        try:
            merged[key] = max(0, int(value))
        except (TypeError, ValueError):
            raise ValueError(f"XP value for {key} must be an integer")

    skill_settings_collection.update_one(
        {"_id": SETTINGS_DOC_ID},
        {"$set": {"xp": merged, "updatedAt": _now(), "updatedBy": str(actor.get("id"))}},
        upsert=True)
    audit("xp_config_update", actor, {"changes": {
        k: {"from": current[k], "to": merged[k]} for k in changes}})
    return merged


def get_badge_rules():
    doc = skill_settings_collection.find_one({"_id": SETTINGS_DOC_ID})
    if doc and isinstance(doc.get("badges"), dict):
        return doc["badges"]
    return {}


def update_badge_rules(rules, actor):
    if not isinstance(rules, dict) or not rules.get("progress", []) and not rules.get("proficiency"):
        raise ValueError("badge rules payload must include progress or proficiency")
    skill_settings_collection.update_one(
        {"_id": SETTINGS_DOC_ID},
        {"$set": {"badges": rules, "updatedAt": _now(), "updatedBy": str(actor.get("id"))}},
        upsert=True)
    audit("badge_rules_update", actor, {"rules": rules})
    return rules


# ------------------------------------------------------------------- core --
def _now():
    return datetime.datetime.utcnow()


def award_xp(student_id, topic_id, reason, xp, award_key, activity_type,
             activity_ref=None, description=None):
    """Idempotently grant XP for one completed eligible activity.

    Returns dict {awarded, xp, duplicate, total_xp}.
    The unique index on award_key is the last line of defence; we also
    pre-check so a benign double click does not surface a raw DuplicateKey.
    """
    if xp <= 0:
        return {"awarded": False, "xp": 0, "duplicate": False, "total_xp": _total_xp(student_id)}

    existing = skill_xp_transactions_collection.find_one({"award_key": award_key})
    if existing:
        return {"awarded": False, "xp": existing.get("xp", xp),
                "duplicate": True, "total_xp": _total_xp(student_id)}

    try:
        doc = {
            "student_id": student_id,
            "topic_id": topic_id,
            "reason": reason,
            "xp": int(xp),
            "award_key": award_key,
            "activity_type": activity_type,
            "activity_ref": activity_ref or award_key,
            "at": _now(),
        }
        skill_xp_transactions_collection.insert_one(doc)
    except Exception as exc:  # pymongo DuplicateKeyError from the race window
        if "duplicate key error" in str(exc).lower() or "E11000" in str(exc):
            return {"awarded": False, "xp": xp, "duplicate": True,
                    "total_xp": _total_xp(student_id)}
        raise

    log_activity(student_id, topic_id, activity_type, activity_ref or award_key,
                 description or f"{reason} (+{xp} XP)", xp=xp)
    return {"awarded": True, "xp": int(xp), "duplicate": False,
            "total_xp": _total_xp(student_id)}


def grant_progress_badge(student_id, topic_id, badge_key, badge_label, percent):
    """Idempotent progress-badge award for (student, topic, badge)."""
    filter_q = {"student_id": student_id, "topic_id": topic_id, "badge_key": badge_key}
    if skill_badge_awards_collection.find_one(filter_q):
        return {"awarded": False, "duplicate": True}
    try:
        skill_badge_awards_collection.insert_one({
            **filter_q,
            "badge_label": badge_label,
            "completion_pct": percent,
            "at": _now(),
        })
    except Exception as exc:
        if "duplicate key error" in str(exc).lower() or "E11000" in str(exc):
            return {"awarded": False, "duplicate": True}
        raise
    log_activity(student_id, topic_id, f"badge:{badge_key}", badge_key,
                 f"Progress badge unlocked: {badge_label}")
    return {"awarded": True, "duplicate": False}


def grant_proficiency_badge(student_id, topic_id, rule_key, label):
    return grant_progress_badge(student_id, topic_id, rule_key, label, 100)


def log_activity(student_id, topic_id, activity_type, activity_ref,
                 description, xp=0, meta=None):
    doc = {
        "student_id": student_id,
        "topic_id": topic_id,
        "activity_type": activity_type,
        "activity_ref": str(activity_ref),
        "description": description,
        "xp": int(xp or 0),
        "meta": meta or {},
        "at": _now(),
    }
    skill_activity_history_collection.insert_one(doc)
    return doc


def audit(action, actor, details):
    skill_audit_log_collection.insert_one({
        "action": action,
        "actor_id": actor.get("id"),
        "actor_role": actor.get("role"),
        "details": details,
        "at": _now(),
    })


def _total_xp(student_id):
    pipeline = [
        {"$match": {"student_id": student_id}},
        {"$group": {"_id": None, "total": {"$sum": "$xp"}}},
    ]
    result = list(skill_xp_transactions_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0


def topic_total_xp(student_id, topic_id):
    pipeline = [
        {"$match": {"student_id": student_id, "topic_id": topic_id}},
        {"$group": {"_id": None, "total": {"$sum": "$xp"}}},
    ]
    result = list(skill_xp_transactions_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0


# ------------------------------------------------------ event integrations --
def problem_difficulty_xp(difficulty, config=None):
    config = config or get_xp_config()
    return {
        "easy": config["problem_easy"],
        "medium": config["problem_medium"],
        "hard": config["problem_hard"],
    }.get((difficulty or "easy").lower(), config["problem_easy"])


def assessment_pass_xp(pct, is_pass, pass_score, config=None):
    """XP for an assessment attempt (awarded once via attempt award_key)."""
    config = config or get_xp_config()
    if not is_pass:
        return 0, None   # failed attempts award nothing
    keys = ["assessment_pass"]
    xp = config["assessment_pass"]
    if pct is not None and pct >= config["high_score_threshold"]:
        xp += config["assessment_high_score_bonus"]
        keys.append("assessment_high_score_bonus")
    return xp, keys
