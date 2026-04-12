"""
/api/analyze — Free keyword analysis endpoint.
Zero API cost. Plan-gated via plan_service.
"""
from flask import Blueprint, request, jsonify, session, current_app
from services.file_service import extract_text, validate_file
from services.keyword_service import analyze_resume_free, get_full_analysis
from services.plan_service import get_features, can_scan

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analysis endpoint.
    Accepts: multipart/form-data with 'resume' file + 'job_description' text
    Returns: ATS score + keyword data (visibility depends on plan)
    """
    try:
        # Validate inputs
        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded"}), 400

        file = request.files["resume"]
        jd_text = request.form.get("job_description", "").strip()

        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if not jd_text or len(jd_text) < 2:
            jd_text = ""

        # Read and validate file
        file_bytes = file.read()
        validate_file(file_bytes, file.filename)

        # Extract text from PDF/DOCX
        resume_text = extract_text(file_bytes, file.filename)

        if not resume_text or len(resume_text) < 100:
            return jsonify({"error": "Could not extract text from your resume. Please ensure it's not a scanned image."}), 400

        # Store resume text in session for later optimization
        session["resume_text"] = resume_text
        session["jd_text"] = jd_text

        # Determine user context from session
        user = session.get("user") or {}
        user_type = user.get("user_type", "student") if user else "guest"
        plan = user.get("plan", "free") if user else "guest"
        scans_used = session.get("scans_used", 0)

        # Plan-gated scan limit check
        if not can_scan(user_type, plan, scans_used):
            return jsonify({"error": "Scan limit reached", "code": "LIMIT_REACHED"}), 402

        session["scans_used"] = scans_used + 1
        features = get_features(user_type, plan)
        show_full = features.get("full_keywords", False)

        if show_full:
            # Free (logged in) / Single / Pro — full keyword visibility
            full = get_full_analysis(resume_text, jd_text)
            return jsonify({
                "success": True,
                "score": full["score"],
                "matched_count": full["matched_count"],
                "missing_count": full["missing_count"],
                "total_keywords": full["total_keywords"],
                "visible_matched": full["matched_keywords"],
                "visible_missing": full["missing_keywords"],
                "blurred_matched_count": 0,
                "blurred_missing_count": 0,
                "is_pro": plan in ("single", "pro"),
                "features": features,
                "score_label": _score_label(full["score"])
            })

        # Guest users — limited view (3 keywords visible, rest blurred)
        result = analyze_resume_free(resume_text, jd_text)
        return jsonify({
            "success": True,
            "score": result["score"],
            "matched_count": result["matched_count"],
            "missing_count": result["missing_count"],
            "total_keywords": result["total_keywords"],
            "visible_matched": result["visible_matched"],
            "blurred_matched_count": result["blurred_matched_count"],
            "blurred_missing_count": result["blurred_missing_count"],
            "is_pro": False,
            "features": features,
            "score_label": _score_label(result["score"])
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Analyze error: {e}")
        return jsonify({"error": "Analysis failed. Please try again."}), 500


def _score_label(score: int) -> str:
    if score >= 75:
        return "strong"
    elif score >= 50:
        return "moderate"
    else:
        return "weak"
