from flask import Blueprint, session, jsonify, request
from functools import wraps

auth_bp = Blueprint("auth", __name__)

def require_paid_session(f):
    """Decorator: requires payment_verified in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("payment_verified") and not session.get("is_admin"):
            return jsonify({
                "error": "Payment required",
                "code": "PAYMENT_REQUIRED"
            }), 402
        return f(*args, **kwargs)
    return decorated

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@auth_bp.route("/me", methods=["GET"])
def get_me():
    user = session.get("user")
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False}), 401

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "")
    password = data.get("password", "")
    
    # Custom dev-admin hook for testing
    if email == "aaditchandra2212@gmail.com" and password == "Admin#2026":
        admin_user = {
            "id": "dev-admin-999",
            "email": email,
            "name": "Aadit Chandra",
            "role": "admin",
            "plan": "pro"
        }
        session["user"] = admin_user
        session["payment_verified"] = True
        session["is_admin"] = True
        return jsonify({"success": True, "user": admin_user})
        
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})
