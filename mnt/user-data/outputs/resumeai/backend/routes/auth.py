"""
/api/auth — Supabase authentication endpoints.
Handles Google OAuth session management.
"""
import os
from flask import Blueprint, request, jsonify, session
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

auth_bp = Blueprint("auth", __name__)


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@auth_bp.route("/auth/session", methods=["POST"])
def set_session():
    """
    Called after Google OAuth completes on frontend.
    Stores user info in Flask session.
    """
    try:
        data = request.get_json()
        access_token = data.get("access_token")
        user = data.get("user", {})

        if not access_token or not user:
            return jsonify({"error": "Invalid session data"}), 400

        # Verify token with Supabase
        supabase = get_supabase()
        user_response = supabase.auth.get_user(access_token)

        if not user_response.user:
            return jsonify({"error": "Invalid token"}), 401

        # Store in Flask session
        session["user_id"] = user_response.user.id
        session["user_email"] = user_response.user.email
        session["user_name"] = user_response.user.user_metadata.get("full_name", "")
        session["access_token"] = access_token

        # Check if this is a new user
        is_new = data.get("is_new_user", False)

        return jsonify({
            "success": True,
            "user": {
                "id": session["user_id"],
                "email": session["user_email"],
                "name": session["user_name"],
            },
            "is_new_user": is_new
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    """Return current user from session."""
    if not session.get("user_id"):
        return jsonify({"authenticated": False}), 401

    return jsonify({
        "authenticated": True,
        "user": {
            "id": session["user_id"],
            "email": session["user_email"],
            "name": session["user_name"],
        }
    })


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Clear session."""
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/auth/usage", methods=["GET"])
def usage():
    """
    Return free tier usage for current IP/user.
    Tracks against 3/day free limit.
    """
    analyses_used = session.get("analyses_used", 0)
    free_limit = int(os.environ.get("FREE_ANALYSIS_LIMIT", 3))

    return jsonify({
        "analyses_used": analyses_used,
        "free_limit": free_limit,
        "remaining": max(0, free_limit - analyses_used),
        "limit_reached": analyses_used >= free_limit
    })
