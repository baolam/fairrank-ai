"""CRUD operations for job postings and candidate applications."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.storage.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(title: str, description: str) -> Dict[str, Any]:
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    created_at = _now()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO jobs (id, title, description, created_at) VALUES (?, ?, ?, ?)",
            (job_id, title, description, created_at),
        )
        conn.commit()
    return {
        "id": job_id,
        "title": title,
        "description": description,
        "created_at": created_at,
        "application_count": 0,
    }


def list_jobs() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT j.id, j.title, j.description, j.created_at,
                   COUNT(a.id) AS application_count
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            GROUP BY j.id
            ORDER BY j.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, title, description, created_at FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
    return dict(row) if row else None


def create_application(
    job_id: str,
    candidate_name: str,
    declared_group: Optional[str],
    resume_raw_text: str,
    resume_redacted_text: str,
    skills: List[str],
    years_of_experience: Optional[float],
) -> Dict[str, Any]:
    app_id = f"app_{uuid.uuid4().hex[:10]}"
    submitted_at = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO applications
                (id, job_id, candidate_name, declared_group, resume_raw_text,
                 resume_redacted_text, skills_json, years_of_experience, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app_id,
                job_id,
                candidate_name,
                declared_group,
                resume_raw_text,
                resume_redacted_text,
                json.dumps(skills),
                years_of_experience,
                submitted_at,
            ),
        )
        conn.commit()
    return {
        "id": app_id,
        "job_id": job_id,
        "candidate_name": candidate_name,
        "declared_group": declared_group,
        "submitted_at": submitted_at,
    }


def list_applications(job_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM applications WHERE job_id = ? ORDER BY submitted_at ASC",
            (job_id,),
        ).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item["skills"] = json.loads(item.pop("skills_json"))
        results.append(item)
    return results
