"""
File parsing service.
Extracts plain text from PDF and DOCX uploads.
"""
import io
import os


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise ValueError(f"Could not read PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
    except Exception as e:
        raise ValueError(f"Could not read DOCX: {str(e)}")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Route to correct parser based on file extension.
    Returns plain text content of resume.
    """
    ext = os.path.splitext(filename.lower())[1]

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")


def validate_file(file_bytes: bytes, filename: str, max_mb: int = 10) -> None:
    """Validate file size and type before processing."""
    max_bytes = max_mb * 1024 * 1024

    if len(file_bytes) > max_bytes:
        raise ValueError(f"File too large. Maximum size is {max_mb}MB.")

    ext = os.path.splitext(filename.lower())[1]
    if ext not in (".pdf", ".docx", ".doc"):
        raise ValueError("Invalid file type. Please upload a PDF or DOCX file.")
