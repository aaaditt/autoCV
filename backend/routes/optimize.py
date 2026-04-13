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


@optimize_bp.route("/cover-letter", methods=["POST"])
@require_auth
@require_plan(["pro"])
def cover_letter():
    """
    Generate a tailored cover letter using Claude AI.
    Requires: authenticated user with pro plan.
    """
    try:
        data = request.json or {}
        job_title = data.get("job_title", "").strip()
        company = data.get("company", "").strip()
        resume_text = data.get("resume_text", "").strip()
        jd_text = data.get("job_description", "").strip()
        tone = data.get("tone", "professional")

        if not job_title or not company:
            return jsonify({"error": "Job title and company are required"}), 400
        if not resume_text:
            return jsonify({"error": "Resume text is required"}), 400

        from services.claude_service import generate_cover_letter
        result = generate_cover_letter(
            job_title=job_title,
            company=company,
            resume_text=resume_text,
            jd_text=jd_text,
            tone=tone,
        )

        return jsonify({
            "success": True,
            "cover_letter": result["cover_letter"],
        })

    except Exception as e:
        current_app.logger.error(f"Cover letter error: {e}")
        return jsonify({"error": "Cover letter generation failed. Please try again."}), 500
