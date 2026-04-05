from flask import session, jsonify
from functools import wraps


def require_paid_session(f):
    """Decorator: requires payment_verified in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("payment_verified"):
            return jsonify({
                "error": "Payment required",
                "code": "PAYMENT_REQUIRED"
            }), 402
        return f(*args, **kwargs)
    return decorated
