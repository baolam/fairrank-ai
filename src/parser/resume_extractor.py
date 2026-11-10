"""Structured entity extraction and demographic redaction for candidate resumes."""

import re
import sys
import uuid
from typing import List, Optional
import numpy as np
from pydantic import BaseModel, Field

# Common technical and soft skills dictionary for rapid extraction
TECH_SKILLS_TAXONOMY = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "golang", "go", "ruby", "rust", "php", "scala", "swift", "kotlin",
    # Frameworks & Libraries
    "fastapi", "flask", "django", "react", "vue", "angular", "next.js", "nodejs", "node.js", "express", "spring", "spring boot",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "spacy", "huggingface", "transformers", "opencv",
    # Cloud & DevOps
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "ci/cd", "terraform", "ansible", "jenkins", "git", "github", "gitlab",
    # Databases & Big Data
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "sqlite", "spark", "kafka", "hadoop", "airflow",
    # Concepts & Methodologies
    "rest", "restful", "graphql", "microservices", "distributed systems", "agile", "scrum", "system design", "machine learning", "deep learning", "nlp", "computer vision", "data engineering"
}


class ParsedResume(BaseModel):
    """Structured representation of a parsed resume."""
    candidate_id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    predicted_name: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    raw_text: str
    redacted_text: str
    detected_sensitive_entities: List[str] = Field(default_factory=list)


def extract_predicted_name(text: str, filename_hint: Optional[str] = None) -> Optional[str]:
    """Heuristically extracts candidate name from header or filename."""
    # 1. Check filename if it looks like a name (e.g., John_Doe_Resume.pdf)
    if filename_hint:
        clean_hint = re.sub(r"\.(pdf|docx|txt)$", "", filename_hint, flags=re.IGNORECASE)
        clean_hint = re.sub(r"(?i)(resume|cv|profile|curriculum|vitae)[_-]?", "", clean_hint).strip(" _-")
        parts = re.split(r"[_\s\-]+", clean_hint)
        if 2 <= len(parts) <= 3 and all(p.isalpha() for p in parts):
            return " ".join(p.capitalize() for p in parts)

    # 2. Check first 3 non-empty lines for Candidate: <Name> or Name: <Name> or Title Case Name
    lines = [line.strip() for line in text.split("\n") if line.strip()][:5]
    for line in lines:
        match = re.match(r"^(?:candidate\s*(?:name)?|name)\s*[:\-]\s*([a-zA-Z\s\.\-]{2,40})$", line, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate

    for line in lines:
        # Ignore obvious section headers
        if re.search(r"(?i)\b(resume|curriculum|vitae|summary|profile|experience|education|skills|contact)\b", line):
            continue
        # Check if line looks like a 2-3 word human name
        words = line.split()
        if 2 <= len(words) <= 3 and all(
            w.replace(".", "").replace("'", "").isalpha() and (w[0].isupper() or w.isupper())
            for w in words
        ):
            return line.strip()

    return None


def extract_skills(text: str) -> List[str]:
    """Extracts known tech and engineering skills from resume text."""
    lowered = text.lower()
    found = set()
    for skill in TECH_SKILLS_TAXONOMY:
        # Match as whole word/phrase
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lowered):
            found.add(skill.title() if len(skill) > 3 else skill.upper())
    return sorted(list(found))


_SKILL_LIST = sorted(TECH_SKILLS_TAXONOMY)
_sbert_ranker_instance = None
_skill_embeddings_cache: Optional[np.ndarray] = None


def _get_semantic_skill_matcher():
    """Lazily loads the SBERT model and precomputes skill-taxonomy embeddings (cached after first call)."""
    global _sbert_ranker_instance, _skill_embeddings_cache
    if _skill_embeddings_cache is None:
        from src.models.sbert_ranker import SBERTRanker
        _sbert_ranker_instance = SBERTRanker()
        _skill_embeddings_cache = _sbert_ranker_instance.encode_batch(_SKILL_LIST)
    return _sbert_ranker_instance, _skill_embeddings_cache


def extract_skills_semantic(text: str, similarity_threshold: float = 0.45) -> List[str]:
    """Catches skill mentions phrased differently from the exact taxonomy term, via SBERT embedding similarity."""
    chunks = [c.strip() for c in re.split(r"[\n.;,]", text) if len(c.strip()) >= 8]
    if not chunks:
        return []

    ranker, skill_embeddings = _get_semantic_skill_matcher()
    chunk_embeddings = ranker.encode_batch(chunks)
    similarities = chunk_embeddings @ skill_embeddings.T

    found = set()
    for idx, skill in enumerate(_SKILL_LIST):
        if similarities[:, idx].max() >= similarity_threshold:
            found.add(skill.title() if len(skill) > 3 else skill.upper())
    return sorted(found)


def extract_experience_years(text: str) -> Optional[float]:
    """Estimates years of professional experience mentioned in text."""
    # Look for patterns like "5+ years", "3 years of experience", "7 yrs experience"
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:professional\s+|specialized\s+)?(?:experience|expertise)",
        r"(?:experience|specializing)\s*(?:of|for|with)?\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None


def redact_sensitive_information(text: str, target_name: Optional[str] = None) -> tuple[str, List[str]]:
    """Redacts name, email, phone numbers, and demographic proxies."""
    redacted = text
    detected = []

    # 1. Redact target name or Candidate: <name>
    if target_name:
        pattern = r"\b" + re.escape(target_name) + r"\b"
        if re.search(pattern, redacted, re.IGNORECASE):
            redacted = re.sub(pattern, "[CANDIDATE_NAME]", redacted, flags=re.IGNORECASE)
            detected.append(f"Name: {target_name}")

    header_name_pattern = r"(?i)(Candidate:\s*)([a-zA-Z\s]{2,40})"
    if re.search(header_name_pattern, redacted):
        redacted = re.sub(header_name_pattern, r"\1[CANDIDATE_NAME]", redacted)
        detected.append("Candidate Header Name")

    # 2. Redact Emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    if re.search(email_pattern, redacted):
        redacted = re.sub(email_pattern, "[EMAIL_REDACTED]", redacted)
        detected.append("Email Address")

    # 3. Redact Phone Numbers
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    if re.search(phone_pattern, redacted):
        redacted = re.sub(phone_pattern, "[PHONE_REDACTED]", redacted)
        detected.append("Phone Number")

    # 4. Redact LinkedIn / GitHub handles
    url_pattern = r"https?://(?:www\.)?(?:linkedin\.com/in|github\.com)/[A-Za-z0-9_-]+"
    if re.search(url_pattern, redacted):
        redacted = re.sub(url_pattern, "[PROFILE_LINK_REDACTED]", redacted)
        detected.append("Social Profile URL")

    return redacted, list(set(detected))


def extract_resume_entities(
    text: str,
    filename_hint: Optional[str] = None,
    candidate_id: Optional[str] = None,
    use_semantic_skills: bool = True,
) -> ParsedResume:
    """End-to-end parser turning raw document text into structured ParsedResume."""
    predicted_name = extract_predicted_name(text, filename_hint)
    skills = set(extract_skills(text))
    if use_semantic_skills:
        try:
            skills |= set(extract_skills_semantic(text))
        except Exception as e:
            # Degrade to regex-only matches if the SBERT model can't be loaded (e.g. no internet on first download).
            print(f"[resume_extractor] semantic skill matching unavailable, falling back to regex: {e}", file=sys.stderr)
    skills = sorted(skills)
    exp = extract_experience_years(text)
    redacted, sensitive_list = redact_sensitive_information(text, predicted_name)

    cid = candidate_id or f"cand_{uuid.uuid4().hex[:8]}"

    return ParsedResume(
        candidate_id=cid,
        predicted_name=predicted_name or "Anonymous Candidate",
        skills=skills,
        years_of_experience=exp,
        raw_text=text,
        redacted_text=redacted,
        detected_sensitive_entities=sensitive_list,
    )
