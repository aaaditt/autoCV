"""
plan_service.py — Single source of truth for plan feature gates.
Both backend routes and frontend auth.js mirror this matrix.
"""

PLAN_FEATURES = {
    "guest": {
        "weekly_scans": 1, "ai_rewrite": False, "download": False,
        "full_keywords": False, "rewrites_remaining": 0,
        "cover_letter": False, "templates": False,
    },
    "free": {
        "weekly_scans": 3, "ai_rewrite": False, "download": False,
        "full_keywords": True, "rewrites_remaining": 0,
        "cover_letter": False, "templates": False,
    },
    "single": {
        "weekly_scans": 999, "ai_rewrite": True, "download": True,
        "full_keywords": True, "rewrites_remaining": 1,
        "cover_letter": False, "templates": True,
    },
    "pro": {
        "weekly_scans": -1, "ai_rewrite": True, "download": True,
        "full_keywords": True, "rewrites_remaining": -1,
        "cover_letter": True, "templates": True,
    },
}

RECRUITER_PLAN_FEATURES = {
    "free": {
        "batch_size": 5,        # Hard cap — blocked beyond this
        "overage_allowed": False,
        "overage_cost_per_resume": 0,
        "csv_export": False,
        "saved_presets": False,
    },
    "pro": {
        "batch_size": 50,       # 50 included, then $1/resume overage
        "overage_allowed": True,
        "overage_cost_per_resume": 1.00,
        "csv_export": True,
        "saved_presets": True,
    },
}


def get_features(user_type: str, plan: str) -> dict:
    if user_type == "recruiter":
        return RECRUITER_PLAN_FEATURES.get(plan, RECRUITER_PLAN_FEATURES["free"])
    return PLAN_FEATURES.get(plan, PLAN_FEATURES["free"])


def can_scan(user_type: str, plan: str, scans_used: int) -> bool:
    limit = get_features(user_type, plan).get("weekly_scans", 0)
    return limit == -1 or scans_used < limit


def can_rewrite(plan: str, rewrites_used: int = 0) -> bool:
    limit = PLAN_FEATURES.get(plan, {}).get("rewrites_remaining", 0)
    return limit == -1 or rewrites_used < limit


def check_batch_limit(plan: str, count: int) -> dict:
    """
    Check if a recruiter batch scan is allowed and calculate overage.
    Returns: {allowed, overage_count, overage_cost, message}
    """
    features = RECRUITER_PLAN_FEATURES.get(plan, RECRUITER_PLAN_FEATURES["free"])
    limit = features["batch_size"]
    overage_allowed = features.get("overage_allowed", False)
    cost_per = features.get("overage_cost_per_resume", 0)

    if count <= limit:
        return {
            "allowed": True,
            "overage_count": 0,
            "overage_cost": 0,
            "message": None,
        }

    if not overage_allowed:
        return {
            "allowed": False,
            "overage_count": 0,
            "overage_cost": 0,
            "message": f"Your plan allows up to {limit} resumes per batch. Upgrade to Pro for larger batches.",
        }

    # Pro plan — allow with overage charge
    overage = count - limit
    cost = round(overage * cost_per, 2)
    return {
        "allowed": True,
        "overage_count": overage,
        "overage_cost": cost,
        "message": f"{overage} extra resume{'s' if overage != 1 else ''} at ${cost_per:.0f} each (${cost:.2f} total)",
    }
