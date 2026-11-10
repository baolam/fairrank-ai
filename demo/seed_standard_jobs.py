"""Script to standardize jobs in fairrank.db and seed at least 50+ diverse candidates per job."""

import json
from pathlib import Path
from src.storage.db import get_connection
from src.parser.document_loader import load_text_from_bytes
from src.parser.resume_extractor import (
    extract_predicted_name,
    extract_skills,
    extract_experience_years,
    redact_sensitive_information,
)

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_resumes"
MANIFEST_PATH = SAMPLE_DIR / "manifest_100.json"

JOBS_SPEC = [
    {
        "id": "job_fullstack_audit",
        "title": "Senior Full-Stack Software Engineer (Audit Benchmark Pool)",
        "description": (
            "Senior Full-Stack Software Engineer\n"
            "We are seeking an experienced developer with 5+ years of experience in Python, "
            "distributed backend architectures, FastAPI, Docker, and PostgreSQL. "
            "Experience in modern web frameworks (React/Vue), cloud infrastructure (AWS/GCP), "
            "and CI/CD pipelines is strongly preferred."
        ),
        "count": 100,  # All 100 candidates
    },
    {
        "id": "job_backend_engineer",
        "title": "Backend Systems Engineer (FastAPI & Microservices)",
        "description": (
            "Backend Systems Engineer\n"
            "Looking for a Backend Systems Engineer proficient in Python, FastAPI, Django, "
            "PostgreSQL, Redis, Kafka, and Docker. Responsible for building high-concurrency "
            "microservices, robust REST/gRPC APIs, and optimizing database performance."
        ),
        "count": 60,  # 15 per demographic group
    },
    {
        "id": "job_data_engineer",
        "title": "Data Platform Engineer (Spark, Airflow & Cloud Lakehouse)",
        "description": (
            "Data Platform Engineer\n"
            "Seeking a Data Engineer with hands-on experience in Python, Apache Spark, Kafka, "
            "Airflow, SQL, and cloud data warehouses (BigQuery/Snowflake/PostgreSQL). "
            "Focus on building scalable ETL/ELT pipelines and real-time streaming analytics."
        ),
        "count": 60,
    },
    {
        "id": "job_frontend_engineer",
        "title": "Senior Frontend Engineer (React, TypeScript & Tailwind)",
        "description": (
            "Senior Frontend Engineer\n"
            "Looking for a Senior Frontend Engineer specialized in React, TypeScript, Tailwind CSS, "
            "Next.js, and modern state management. Passionate about responsive UI/UX, design systems, "
            "web performance, and client-side architecture."
        ),
        "count": 60,
    },
    {
        "id": "job_ml_engineer",
        "title": "Machine Learning Engineer (NLP, PyTorch & LLMs)",
        "description": (
            "Machine Learning Engineer\n"
            "Seeking an ML Engineer with solid experience in Python, PyTorch, Hugging Face Transformers, "
            "Sentence-BERT, vector databases, and LLM fine-tuning/RAG systems. Knowledge of fair ranking, "
            "bias evaluation, and MLOps deployment is a major plus."
        ),
        "count": 60,
    },
]


def seed_standardized_database():
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Loaded manifest with {len(manifest)} candidate profiles.")

    # Pre-parse all 100 candidate resumes into memory
    parsed_candidates = []
    print("Pre-parsing PDF resumes into cache...")
    for item in manifest:
        pdf_path = Path(item["pdf_path"])
        content = pdf_path.read_bytes()
        raw_text = load_text_from_bytes(content, pdf_path.name)
        name = extract_predicted_name(raw_text, pdf_path.name) or item["name"]
        exp = extract_experience_years(raw_text) or item["experience_years"]
        skills = extract_skills(raw_text)
        redacted_text, _ = redact_sensitive_information(raw_text, name)

        parsed_candidates.append({
            "name": name,
            "group": item["group"],
            "raw_text": raw_text,
            "redacted_text": redacted_text,
            "skills": skills,
            "experience_years": exp,
        })
    print(f"Parsed {len(parsed_candidates)} candidates successfully.")

    # Group candidates by demographic group
    by_group = {}
    for cand in parsed_candidates:
        grp = cand["group"]
        by_group.setdefault(grp, []).append(cand)

    print("Candidates per group:", {k: len(v) for k, v in by_group.items()})

    # Clear old database tables
    with get_connection() as conn:
        conn.execute("DELETE FROM applications")
        conn.execute("DELETE FROM jobs")
        conn.commit()
        print("Cleared old jobs and applications from database.")

    # Insert standardized jobs and applications
    from src.storage import repository

    total_inserted = 0
    for job_info in JOBS_SPEC:
        job = repository.create_job(job_info["title"], job_info["description"])
        job_id = job["id"]
        count = job_info["count"]

        if count >= len(parsed_candidates):
            selected_cands = parsed_candidates
        else:
            per_group = count // len(by_group)
            selected_cands = []
            for grp, cands in by_group.items():
                selected_cands.extend(cands[:per_group])

        for cand in selected_cands:
            repository.create_application(
                job_id=job_id,
                candidate_name=cand["name"],
                declared_group=cand["group"],
                resume_raw_text=cand["raw_text"],
                resume_redacted_text=cand["redacted_text"],
                skills=cand["skills"],
                years_of_experience=cand["experience_years"],
            )
            total_inserted += 1

        print(f"Created '{job_info['title']}' (ID: {job_id}) with {len(selected_cands)} applications.")

    print(f"\nAll done! Successfully seeded {len(JOBS_SPEC)} jobs with {total_inserted} total applications.")


if __name__ == "__main__":
    seed_standardized_database()
