"""
/api/optimize — AI resume rewrite endpoint.
Calls Claude API. Plan-gated to single/pro plans only.
"""
from flask import Blueprint, request, jsonify, session, current_app
from services.claude_service import optimize_resume
from services.keyword_service import get_full_analysis
from routes.auth import require_auth, require_plan

optimize_bp = Blueprint("optimize", __name__)


@optimize_bp.route("/optimize", methods=["POST"])
@require_auth
@require_plan(["single", "pro"])
def optimize():
    """
    Paid optimization endpoint.
    Requires: authenticated user with single or pro plan.
    Returns: optimized resume text + before/after scores.
    """
    try:
        user = session.get("user", {})
        optimization_id = f"opt-{user.get('id', 'unknown')}-{int(__import__('time').time())}"

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
