"""
Claude API service.
ONLY called after plan verification — gated to single/pro plans.
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
    
    IMPORTANT: Only call this after plan verification (single/pro).
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
        model="claude-3-5-sonnet-20240620",

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


COVER_LETTER_SYSTEM_PROMPT = """You are an expert career coach and professional writer. 
Your job is to write compelling, tailored cover letters that:
- Are addressed to the specific company and role
- Highlight relevant experience from the candidate's resume
- Show enthusiasm and cultural fit
- Are concise (250-350 words)
- Follow standard business letter format
- Never fabricate experience or skills
- Match the requested tone

Output ONLY the cover letter text. No commentary, no headers like "Subject:" or "Cover Letter"."""


def generate_cover_letter(
    job_title: str,
    company: str,
    resume_text: str,
    jd_text: str = "",
    tone: str = "professional",
) -> dict:
    """
    Use Claude to generate a tailored cover letter.
    Pro plan only.
    """
    tone_instructions = {
        "professional": "Use a professional, confident tone.",
        "enthusiastic": "Use an enthusiastic, passionate tone that shows excitement for the role.",
        "conversational": "Use a warm, conversational tone that feels personal and approachable.",
        "formal": "Use a formal, corporate tone appropriate for traditional industries.",
    }
    tone_desc = tone_instructions.get(tone, tone_instructions["professional"])

    prompt = f"""Write a cover letter for the following role:

POSITION: {job_title} at {company}
TONE: {tone_desc}

{"JOB DESCRIPTION:" if jd_text else ""}
{jd_text[:2000] if jd_text else "No job description provided — write a general cover letter for this role."}

CANDIDATE'S RESUME:
{resume_text[:3000]}

Write a compelling cover letter that connects the candidate's experience to this role."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",

        max_tokens=1500,
        system=COVER_LETTER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "cover_letter": message.content[0].text.strip(),
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }
