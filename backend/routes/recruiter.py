"""
/api/recruiter/batch-scan — Multi-resume ATS scanning for HR users.
Guest: 3 resumes (demo). Free recruiter: 5 (hard cap). Pro recruiter: 50 included, $1/resume after.
"""
from flask import Blueprint, request, jsonify, session
from services.keyword_service import extract_jd_keywords, score_resume_against_jd
from services.file_service import extract_text, validate_file
from services.plan_service import get_features, check_batch_limit

recruiter_bp = Blueprint("recruiter", __name__)


@recruiter_bp.route("/recruiter/batch-scan", methods=["POST"])
def batch_scan():
    user = session.get("user") or {}
    user_type = user.get("user_type", "student")
    plan = user.get("plan", "free")

    files = request.files.getlist("resumes")
    jd_text = request.form.get("job_description", "").strip()
    keywords_raw = request.form.get("keywords", "")

    if not files:
        return jsonify({"error": "No resumes uploaded"}), 400

    # Guest gets a small demo batch (3 resumes)
    if not user:
        if len(files) > 3:
            return jsonify({
                "error": "Sign up for a free recruiter account to scan more than 3 resumes",
                "code": "GUEST_LIMIT"
            }), 402
    else:
        # Logged-in recruiter — check plan batch limits
        batch_check = check_batch_limit(plan, len(files))
        if not batch_check["allowed"]:
            return jsonify({
                "error": batch_check["message"],
                "code": "BATCH_LIMIT"
            }), 402

    # Extract JD keywords (from text or manual comma-separated input)
    jd_keywords = (
        [k.strip() for k in keywords_raw.split(",") if k.strip()]
        if keywords_raw else extract_jd_keywords(jd_text)
    )

    results = []
    for file in files:
        try:
            fb = file.read()
            validate_file(fb, file.filename)
            text = extract_text(fb, file.filename)
            data = score_resume_against_jd(text, jd_keywords)
            results.append({
                "filename": file.filename,
                "score": data["score"],
                "matched_keywords": data["matched_keywords"],
                "missing_keywords": data["missing_keywords"],
                "matched_count": data["matched_count"],
                "missing_count": data["missing_count"],
            })
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e), "score": 0})

    # Sort by score descending (best candidates first)
    results.sort(key=lambda r: r.get("score", 0), reverse=True)

    # Calculate overage for logged-in pro recruiters
    overage_info = {}
    if user:
        batch_check = check_batch_limit(plan, len(files))
        if batch_check["overage_count"] > 0:
            overage_info = {
                "overage_count": batch_check["overage_count"],
                "overage_cost": batch_check["overage_cost"],
                "overage_message": batch_check["message"],
            }

    return jsonify({
        "success": True,
        "results": results,
        "keywords_used": jd_keywords,
        "total_scanned": len(results),
        **overage_info,
    })
