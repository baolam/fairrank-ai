"""Unit tests for document loader, resume extractor, and sensitive redaction."""

import pytest
from src.parser.document_loader import load_text_from_bytes
from src.parser.resume_extractor import (
    extract_predicted_name,
    extract_skills,
    extract_experience_years,
    redact_sensitive_information,
    extract_resume_entities,
)


def test_extract_skills_and_experience():
    text = """
    Jane Doe
    Email: jane.doe@example.com | Phone: +1-555-123-4567
    Summary: Senior Python Developer with 6 years of experience in FastAPI, Docker, and PostgreSQL.
    Skills: Python, Docker, PostgreSQL, React, AWS, Git.
    """
    skills = extract_skills(text)
    assert "Python" in skills
    assert "Fastapi" in skills or "FASTAPI" in skills
    assert "Docker" in skills
    assert "Postgresql" in skills

    exp = extract_experience_years(text)
    assert exp == 6.0


def test_name_extraction_and_redaction():
    text = """Candidate: Jamal Washington
    Experienced Software Engineer with 5+ years experience in Python and Docker.
    Contact: jamal.w@example.com
    """
    name = extract_predicted_name(text)
    assert name == "Jamal Washington"

    redacted, sensitive = redact_sensitive_information(text, name)
    assert "[CANDIDATE_NAME]" in redacted
    assert "Jamal Washington" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert len(sensitive) >= 2


def test_load_text_from_bytes_txt():
    raw_content = b"Candidate: Brad Miller\nLead Engineer with Docker and AWS experience."
    text = load_text_from_bytes(raw_content, "brad_resume.txt")
    assert "Candidate: Brad Miller" in text
    parsed = extract_resume_entities(text, filename_hint="brad_resume.txt")
    assert parsed.predicted_name == "Brad Miller"
    assert "Docker" in parsed.skills
    assert "Aws" in parsed.skills or "AWS" in parsed.skills
