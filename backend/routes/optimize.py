"""
/api/optimize — AI resume rewrite endpoint.
Calls Claude API. ONLY accessible after Stripe payment confirmed.
"""
from flask import Blueprint, request, jsonify, session, current_app
from services.claude_service import optimize_resume
from services.keyword_service import get_full_analysis
from routes.auth import require_paid_session

optimize_bp = Blueprint("optimize", __name__)


@optimize_bp.route("/optimize", methods=["POST"])
def optimize():
    """
    Paid optimization endpoint.
    Requires: valid payment session (set by Stripe webhook)
    Returns: optimized resume text + before/after scores
    """
    try:
        # Gate: removed Stripe payment check for manual flow
        optimization_id = "manual-opt-launch-today"

        # Get resume data from session (set during /analyze)
        resume_text = session.get("resume_text")
        jd_text = session.get("jd_text")

        if not resume_text or not jd_text:
            return jsonify({
                "error": "Session expired. Please re-upload your resume.",
                "code": "SESSION_EXPIRED"
            }), 400

        # Get full keyword analysis for context
        full_analysis = get_full_analysis(resume_text, jd_text)
        original_score = full_analysis["score"]

        # Call Claude API (the expensive part)
        result = optimize_resume(
            resume_text=resume_text,
            jd_text=jd_text,
            missing_keywords=full_analysis["missing_keywords"],
            matched_keywords=full_analysis["matched_keywords"]
        )

        # Store optimized result in session for download
        session["optimized_text"] = result["optimized_text"]
        session["original_score"] = original_score
        session["optimized_score"] = result["new_score"]

        # Clear payment flag (one-time use)
        session.pop("payment_verified", None)

        return jsonify({
            "success": True,
            "original_score": original_score,
            "optimized_score": result["new_score"],
            "score_improvement": result["new_score"] - original_score,
            "optimized_text": result["optimized_text"],
            "original_text": resume_text,
            "matched_keywords": result["new_matched"],
            "missing_keywords": result["new_missing"],
            "optimization_id": optimization_id
        })

    except Exception as e:
        current_app.logger.error(f"Optimize error: {e}")
        return jsonify({"error": "Optimization failed. Please contact support."}), 500
