"""Helper script to create a demo job posting and ingest all 100 sample resumes into the database.

Enables instant live testing of 100-candidate ranking, Pareto sweeps, and compliance reports
in the Recruiter Workspace without needing to upload files manually one by one.
"""

import json
from pathlib import Path
from src.storage import repository
from src.parser.document_loader import load_text_from_bytes
from src.parser.resume_extractor import (
    extract_predicted_name,
    extract_skills,
    extract_experience_years,
    redact_sensitive_information,
)

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_resumes"
MANIFEST_PATH = SAMPLE_DIR / "manifest_100.json"


def seed_job_with_100_resumes():
    if not MANIFEST_PATH.exists():
        print("Manifest 100 not found. Run demo/generate_100_resumes.py first.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    job_title = "Senior Full-Stack Software Engineer (100-Candidate Audit Pool)"
    job_description = (
        "Senior Full-Stack Software Engineer\n"
        "We are seeking an experienced developer with 5+ years of experience in Python, "
        "distributed backend architectures, FastAPI, Docker, and PostgreSQL. "
        "Experience in modern web frameworks (React/Vue), cloud infrastructure (AWS/GCP), "
        "and CI/CD pipelines is strongly preferred."
    )

    print(f"Creating demo job: '{job_title}'...")
    job = repository.create_job(job_title, job_description)
    job_id = job["id"]
    print(f"Job created with ID: {job_id}")

    print(f"Ingesting 100 applications for {job_id}...")
    ingested_count = 0

    for item in manifest:
        pdf_path = Path(item["pdf_path"])
        content = pdf_path.read_bytes()
        raw_text = load_text_from_bytes(content, pdf_path.name)
        name = extract_predicted_name(raw_text, pdf_path.name) or item["name"]
        exp = extract_experience_years(raw_text) or item["experience_years"]
        skills = extract_skills(raw_text)
        redacted_text, _ = redact_sensitive_information(raw_text, name)

        repository.create_application(
            job_id=job_id,
            candidate_name=name,
            declared_group=item["group"],
            resume_raw_text=raw_text,
            resume_redacted_text=redacted_text,
            skills=skills,
            years_of_experience=exp,
        )
        ingested_count += 1

    print(f"Successfully loaded all {ingested_count} candidate applications into database for job {job_id}!")
    print("You can now select this job in the Recruiter Dashboard to run 100-candidate ranking & fairness audits.")
    return job_id


if __name__ == "__main__":
    seed_job_with_100_resumes()
