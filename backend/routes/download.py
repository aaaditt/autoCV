"""
/api/download — Serve optimized resume as PDF or DOCX.
"""
import io
from flask import Blueprint, request, send_file, jsonify, session

download_bp = Blueprint("download", __name__)


@download_bp.route("/download/<format>", methods=["GET"])
def download(format: str):
    """
    Download optimized resume.
    format: 'pdf' or 'docx'
    """
    try:
        optimized_text = session.get("optimized_text")

        if not optimized_text:
            return jsonify({
                "error": "No optimized resume found. Please complete optimization first."
            }), 404

        if format == "pdf":
            from services.document_service import generate_pdf
            file_bytes = generate_pdf(optimized_text)
            mimetype = "application/pdf"
            filename = "optimized_resume.pdf"

        elif format == "docx":
            from services.document_service import generate_docx
            file_bytes = generate_docx(optimized_text)
            mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = "optimized_resume.docx"

        else:
            return jsonify({"error": "Invalid format. Use 'pdf' or 'docx'"}), 400

        from flask import make_response
        response = make_response(send_file(
            io.BytesIO(file_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        ))
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500
