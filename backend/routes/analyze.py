"""
/api/analyze — Free keyword analysis endpoint.
Zero API cost. Rate limited to 3/day per IP.
"""
from flask import Blueprint, request, jsonify, current_app
from services.file_service import extract_text, validate_file
from services.keyword_service import analyze_resume_free

analyze_bp = Blueprint("analyze", __name__)


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Free analysis endpoint.
    Accepts: multipart/form-data with 'resume' file + 'job_description' text
    Returns: ATS score + partial keyword data (rest blurred on frontend)
    """
    try:
        # Validate inputs
        if "resume" not in request.files:
            return jsonify({"error": "No resume file uploaded"}), 400

        file = request.files["resume"]
        jd_text = request.form.get("job_description", "").strip()

        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if not jd_text or len(jd_text) < 50:
            return jsonify({"error": "Job description too short. Please paste the full job description."}), 400

        # Read and validate file
        file_bytes = file.read()
        validate_file(file_bytes, file.filename)

        # Extract text from PDF/DOCX
        resume_text = extract_text(file_bytes, file.filename)

        if not resume_text or len(resume_text) < 100:
            return jsonify({"error": "Could not extract text from your resume. Please ensure it's not a scanned image."}), 400

        # Run free local analysis (zero API cost)
        result = analyze_resume_free(resume_text, jd_text)

        # Store resume text in session for later optimization
        # (avoid re-uploading on payment)
        from flask import session
        session["resume_text"] = resume_text
        session["jd_text"] = jd_text

        return jsonify({
            "success": True,
            "score": result["score"],
            "matched_count": result["matched_count"],
            "missing_count": result["missing_count"],
            "total_keywords": result["total_keywords"],
            "visible_matched": result["visible_matched"],
            "blurred_matched_count": result["blurred_matched_count"],
            "blurred_missing_count": result["blurred_missing_count"],
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
