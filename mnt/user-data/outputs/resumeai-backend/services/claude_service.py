"""
Claude API service.
ONLY called after Stripe payment is confirmed.
This is the expensive operation — gate it hard.
"""
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


OPTIMIZE_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) 
resume optimizer and professional resume writer. Your job is to rewrite resumes 
to maximize their match with a specific job description while keeping all 
information truthful and professional.

Rules:
- Never invent experience, skills, or qualifications the candidate doesn't have
- Naturally incorporate missing keywords where they legitimately apply
- Maintain the candidate's voice and tone
- Keep the same resume structure/sections
- Use strong action verbs
- Quantify achievements where possible
- Output ONLY the rewritten resume text, no commentary
- Preserve all contact information exactly as given"""


def optimize_resume(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str],
    matched_keywords: list[str]
) -> dict:
    """
    Use Claude to rewrite resume optimized for the job description.
    Returns optimized text + metadata.
    
    IMPORTANT: Only call this after payment is confirmed.
    """
    missing_str = ", ".join(missing_keywords[:20]) if missing_keywords else "none identified"
    matched_str = ", ".join(matched_keywords[:10]) if matched_keywords else "none"

    prompt = f"""Please optimize this resume for the following job description.

KEYWORDS ALREADY IN RESUME: {matched_str}

MISSING KEYWORDS TO INCORPORATE (where truthfully applicable): {missing_str}

JOB DESCRIPTION:
{jd_text[:3000]}

ORIGINAL RESUME:
{resume_text[:4000]}

Rewrite the resume to maximize ATS score while keeping all information truthful. 
Output only the optimized resume text."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=OPTIMIZE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    optimized_text = message.content[0].text.strip()

    # Calculate approximate improvement
    from services.keyword_service import get_full_analysis
    new_analysis = get_full_analysis(optimized_text, jd_text)

    return {
        "optimized_text": optimized_text,
        "new_score": new_analysis["score"],
        "new_matched": new_analysis["matched_keywords"],
        "new_missing": new_analysis["missing_keywords"],
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }
