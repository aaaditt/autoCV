"""
Keyword analysis engine using spaCy + TF-IDF.
Zero API cost — runs entirely locally.
Used for the free tier analysis.
"""
import re
from collections import Counter

# Common stop words to filter out
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "dare", "ought", "used", "you", "we", "they",
    "he", "she", "it", "i", "my", "your", "our", "their", "this", "that",
    "these", "those", "not", "no", "nor", "so", "yet", "both", "either",
    "neither", "each", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "just", "also", "as", "if", "then", "than",
    "when", "where", "who", "which", "what", "how", "all", "any", "both",
    "experience", "work", "working", "role", "team", "company", "strong",
    "excellent", "good", "great", "ability", "skills", "skill", "including",
    "required", "preferred", "must", "plus", "years", "year", "across",
    "within", "using", "use", "help", "ensure", "support", "responsible",
    "well", "new", "own", "same", "us", "its", "etc", "job", "position"
}

# Generic Keywords for "No JD" Analysis
GENERIC_ATS_KEYWORDS = [
    "Communication", "Management", "Leadership", "Teamwork", 
    "Problem Solving", "Collaboration", "Process Improvement",
    "Strategy", "Analysis", "Development", "Implementation",
    "Design", "Research", "Documentation", "Planning", "Execution",
    "Optimization", "Efficiency", "Results", "Stakeholder Management"
]

# High-value tech/skill patterns
SKILL_PATTERNS = [
    r'\b[A-Z][a-z]+(?:\.[a-z]+)+\b',          # React.js, Node.js
    r'\b[A-Z]{2,}\b',                           # AWS, ML, API, CI/CD
    r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b',      # Machine Learning, Deep Learning
    r'\b\w+(?:\.js|\.py|\.ts)\b',              # react.js, next.js
    r'\b(?:Python|Java|JavaScript|TypeScript|Go|Rust|Swift|Kotlin|Ruby|PHP|C\+\+|C#)\b',
    r'\b(?:React|Angular|Vue|Django|Flask|FastAPI|Spring|Rails|Laravel)\b',
    r'\b(?:AWS|GCP|Azure|Docker|Kubernetes|Terraform|Jenkins|Git|GitHub)\b',
    r'\b(?:SQL|NoSQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b',
    r'\b(?:REST|GraphQL|gRPC|WebSocket|OAuth|JWT|API)\b',
    r'\b(?:TensorFlow|PyTorch|scikit-learn|Pandas|NumPy|OpenCV)\b',
    r'\b(?:Agile|Scrum|Kanban|CI\/CD|DevOps|MLOps)\b',
]


def extract_text_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text without spaCy."""
    keywords = []

    # Extract pattern-based skills first (highest signal)
    for pattern in SKILL_PATTERNS:
        matches = re.findall(pattern, text)
        keywords.extend([m.strip() for m in matches])

    # Extract noun phrases via simple heuristics
    # Split into sentences, find capitalized phrases and technical terms
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#\.\/\-]+\b', text)

    for word in words:
        clean = word.strip().lower()
        if (
            len(clean) > 3
            and clean not in STOP_WORDS
            and not clean.isdigit()
        ):
            keywords.append(clean)

    return keywords


    if not jd_text or len(jd_text.strip()) < 10:
        return GENERIC_ATS_KEYWORDS[:20]  # Return subset of general keywords

    raw_keywords = extract_text_keywords(jd_text)

    # Count frequency
    counts = Counter(raw_keywords)

    # Deduplicate preserving case (prefer uppercase/mixed case over lowercase)
    seen_lower = {}
    for kw, count in counts.most_common():
        lower = kw.lower()
        if lower not in seen_lower:
            seen_lower[lower] = (kw, count)
        else:
            # Keep the one with better casing
            existing_kw, existing_count = seen_lower[lower]
            if kw != kw.lower() and existing_kw == existing_kw.lower():
                seen_lower[lower] = (kw, existing_count + count)

    # Sort by frequency, take top 40
    sorted_keywords = sorted(
        seen_lower.values(),
        key=lambda x: x[1],
        reverse=True
    )

    return [kw for kw, count in sorted_keywords[:40]]


def score_resume_against_jd(resume_text: str, jd_keywords: list[str]) -> dict:
    """
    Score resume against job description keywords.
    Returns match percentage and found/missing keyword lists.
    """
    resume_lower = resume_text.lower()

    matched = []
    missing = []

    for keyword in jd_keywords:
        # Fuzzy match: check for keyword and common variations
        kw_lower = keyword.lower()
        variations = [
            kw_lower,
            kw_lower.replace('.', ''),      # nodejs -> node
            kw_lower.replace('-', ' '),     # ci-cd -> ci cd
            kw_lower.replace('/', ' '),     # ci/cd -> ci cd
            kw_lower + 's',                 # api -> apis
            kw_lower.rstrip('s'),           # apis -> api
        ]

        found = any(var in resume_lower for var in variations)

        if found:
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(jd_keywords)
    score = round((len(matched) / total * 100) if total > 0 else 0)

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "total_keywords": total,
        "matched_count": len(matched),
        "missing_count": len(missing)
    }


def analyze_resume_free(resume_text: str, jd_text: str) -> dict:
    """
    Full free analysis pipeline.
    No API calls — purely local NLP.
    """
    jd_keywords = extract_jd_keywords(jd_text)
    score_data = score_resume_against_jd(resume_text, jd_keywords)

    # For free tier: return score + first 3 matched keywords visible
    # rest are blurred on frontend
    visible_matched = score_data["matched_keywords"][:3]
    blurred_matched = score_data["matched_keywords"][3:]
    blurred_missing = score_data["missing_keywords"]  # all missing are blurred

    return {
        "score": score_data["score"],
        "matched_count": score_data["matched_count"],
        "missing_count": score_data["missing_count"],
        "total_keywords": score_data["total_keywords"],
        "visible_matched": visible_matched,
        "blurred_matched_count": len(blurred_matched),
        "blurred_missing_count": len(blurred_missing),
        # Don't send actual missing keywords — frontend just shows count
    }


def get_full_analysis(resume_text: str, jd_text: str) -> dict:
    """
    Full analysis for paid users — returns all keywords.
    Still no API cost — just removes the blur gate.
    """
    jd_keywords = extract_jd_keywords(jd_text)
    return score_resume_against_jd(resume_text, jd_keywords)
