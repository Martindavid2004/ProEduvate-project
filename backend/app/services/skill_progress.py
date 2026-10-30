"""
Placement Training Skill Card System - progress calculation service.

All progress math lives here as PURE functions (no DB access) so that the
formula is unit-testable and every route returns one consistent answer.

Completion is tracked separately from proficiency:
- completion  = how much of the required work has been done
- proficiency = assessment skill level for the topic (pass metrics, master)
"""

# Agreed formula: Coding 40% + Learning 20% + Assessment 40%.
DEFAULT_CATEGORY_WEIGHTS = {
    "coding": 0.40,
    "learning": 0.20,
    "assessment": 0.40,
}

PROGRESS_BADGES = [
    # (key, label, min %, max % inclusive-exclusive, meaning)
    {"key": "beginner", "label": "Beginner", "min": 0, "max": 25,
     "meaning": "Started the topic and is learning fundamentals."},
    {"key": "practitioner", "label": "Practitioner", "min": 25, "max": 50,
     "meaning": "Building familiarity through lessons and practice."},
    {"key": "advanced", "label": "Advanced", "min": 50, "max": 80,
     "meaning": "Making substantial progress through required activities."},
    {"key": "expert", "label": "Expert", "min": 80, "max": 101,
     "meaning": "Has completed most or all required activities."},
]

# Proficiency (Skill Master) defaults - administratively configurable in the
# skill_badge_rules collection. Rules: >= assessment pct AND all required
# coding problems solved AND >= learning threshold.
DEFAULT_PROFICIENCY_RULE = {
    "key": "skill_master",
    "label": "Skill Master",
    "min_assessment_pct": 80,   # assessment proficiency requirement
    "minimal_learning_pct": 60,  # all required lessons effectively done
    "require_all_problems_solved": True,
}


def completion_component(ratio):
    """Clamp a completed/total ratio to 0..100."""
    if ratio is None or not isinstance(ratio, (int, float)) or isinstance(ratio, bool):
        return 0.0
    if ratio < 0:
        return 0.0
    return min(100.0, ratio * 100.0)


def overall_completion(coding=None, learning=None, assessment=None, weights=None,
                       proficiency_weight_sum=None, include=None):
    """Weighted overall topic completion in 0..100.

    Each component value is 0..1 (completed required / total required).
    Categories with a total of 0 (no required activities) are EXCLUDED and the
    remaining weights are normalised, so a topic without lessons does not lose
    the learning weight silently.
    """
    weights = weights or DEFAULT_CATEGORY_WEIGHTS
    include = include if include is not None else {
        "coding": coding is not None,
        "learning": learning is not None,
        "assessment": assessment is not None,
    }
    components = {"coding": coding, "learning": learning, "assessment": assessment}

    active_weight = 0.0
    active_sum = 0.0
    for category, value in components.items():
        ratio = value if value is not None else 0.0
        if include.get(category):
            active_weight += weights.get(category, 0.0)
            active_sum += completion_component(ratio) * weights.get(category, 0.0)
    if active_weight <= 0:
        return 0.0
    return round(active_sum / active_weight, 2)


def progress_badge(pct, thresholds=None):
    """Progress badge (NOT mastery proof) for a topic completion percent."""
    if pct is None or not isinstance(pct, (int, float)) or isinstance(pct, bool) or pct < 0:
        pct = 0.0
    pct = min(100.0, pct)
    levels = thresholds or PROGRESS_BADGES
    for level in sorted(levels, key=lambda x: x["min"]):
        if level["min"] <= pct < level["max"]:
            return level["key"], level["label"], level["meaning"]
    top = sorted(levels, key=lambda x: x["min"])[-1]
    return top["key"], top["label"], top["meaning"]


def proficiency_status(assessment_pct, learning_pct, all_problems_solved,
                       rule=None):
    """Separate proficiency evaluation (not completion).

    Skill Master requires: high assessment score, near-complete learning, and
    all required coding problems solved (directive 7 + 8 in the task doc).
    Returns (enabled, key, reason) where reason explains what is missing.
    """
    rule = rule or DEFAULT_PROFICIENCY_RULE
    reasons = []
    if (assessment_pct or 0) < rule["min_assessment_pct"]:
        reasons.append(
            f"assessment {assessment_pct}% < required {rule['min_assessment_pct']}%")
    if (learning_pct or 0) < rule["minimal_learning_pct"]:
        reasons.append(
            f"learning {learning_pct}% < required {rule['minimal_learning_pct']}%")
    if rule["require_all_problems_solved"] and not all_problems_solved:
        reasons.append("required coding problems not fully solved")
    if reasons:
        return False, None, "; ".join(reasons)
    return True, rule["key"], "all criteria met"


def build_topic_card(required, state):
    """Build one topic card payload from raw counts.

    required = {'coding': solved_required, 'learning': completed_lessons, 'assessment': completed_assessments, 'problems': total_lessons...}
    state = {'category_ratio': {...}, 'assessment_pct':..., 'learning_pct':...}
    """
    ratios = state.get("category_ratio", {})
    include = {k: v is not None and v > 0 for k, v in required.items()}
    pct = overall_completion(
        coding=ratios.get("coding"),
        learning=ratios.get("learning"),
        assessment=ratios.get("assessment"),
        include=include)
    badge_key, badge_label, badge_meaning = progress_badge(pct)
    prof_ok, prof_key, prof_reason = proficiency_status(
        state.get("assessment_pct", 0), ratios.get("learning", 0),
        state.get("all_problems_solved", False),
        rule=state.get("proficiency_rule"))
    return {
        "required": required,
        "category_ratio": ratios,
        "include": include,
        "completion_pct": pct,
        "badge_key": badge_key,
        "badge_label": badge_label,
        "badge_meaning": badge_meaning,
        "proficiency": {"earned": prof_ok, "key": prof_key, "reason": prof_reason},
    }
