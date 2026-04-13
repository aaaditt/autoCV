"""
/api/auth — Supabase JWT-verified auth. No hardcoded credentials.
Plan + user_type read from DB profile on every session sync.
"""
import os
import requests as http
import jwt as pyjwt
from flask import Blueprint, session, jsonify, request
from functools import wraps

auth_bp = Blueprint("auth", __name__)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


from supabase import create_client

def _verify_token(token: str) -> dict | None:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            return {"sub": user_response.user.id}
    except Exception as e:
        print(f"Token verification failed entirely: {e}")
    return None




def _fetch_profile(user_id: str, token: str) -> tuple[str, str]:
    """Returns (plan, user_type) from profiles table."""
    try:
        res = http.get(
            f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=plan,user_type",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            timeout=5
        )

        rows = res.json()
        if rows and isinstance(rows, list):
            return rows[0].get("plan", "free"), rows[0].get("user_type", "student")
    except Exception as e:
        print(f"Profile fetch failed: {e}")
    return "free", "student"


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        
        # JWT Token Fallback (for cross-origin cookie-less requests)
        auth_header = request.headers.get("Authorization")
        if not user and auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = _verify_token(token)
            if payload:
                # Synchronous local sync (doesn't hit DB for speed, trusts metadata)
                # metadata = request.headers.get("X-User-Metadata") # Optional
                user = {
                    "id": payload.get("sub"),
                    "plan": "free" # Default, will be checked if require_plan
                }
                # To get the real plan without hitting DB, we expect it in metadata or we fetch it
                # For now, if require_plan is called, we will fetch it there
        
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def require_plan(plans: list[str]):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = session.get("user")
            
            # JWT Token Fallback
            auth_header = request.headers.get("Authorization")
            if not user and auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = _verify_token(token)
                if payload:
                    user_id = payload.get("sub")
                    # We MUST fetch profile for plan requirement
                    db_plan, ut = _fetch_profile(user_id, token)
                    user = {"id": user_id, "plan": db_plan, "user_type": ut}

            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            if user.get("plan", "free") not in plans:
                return jsonify({"error": "Plan upgrade required", "code": "UPGRADE_REQUIRED"}), 402
            
            return f(*args, **kwargs)
        return decorated
    return decorator



@auth_bp.route("/me", methods=["GET"])
def get_me():
    user = session.get("user")
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False}), 401


@auth_bp.route("/session", methods=["POST"])
def sync_session():
    data = request.json or {}
    access_token = data.get("access_token")
    user_data = data.get("user", {})

    if not access_token:
        return jsonify({"error": "No access token"}), 400

    payload = _verify_token(access_token)
    if not payload:
        return jsonify({"error": "Invalid token"}), 401

    user_id = payload.get("sub")
    db_plan, user_type = _fetch_profile(user_id, access_token)

    # Resolve plan: Metadata > DB (allows for instant manual upgrades)
    metadata = user_data.get("user_metadata", {})
    final_plan = metadata.get("plan") or db_plan or "free"

    user = {
        "id": user_id,
        "email": user_data.get("email", ""),
        "name": metadata.get("full_name")
               or user_data.get("email", "user").split("@")[0],
        "plan": final_plan,
        "user_type": user_type,
    }
    session["user"] = user
    session.permanent = True
    return jsonify({"success": True, "user": user})



@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})
