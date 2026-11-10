"""Router for job postings and candidate applications.

Backs the role-play demo: a Candidate submits a CV against an open job
posting; a Recruiter (behind the access-code gate) reviews the real
submissions for that job before running the ranking/audit pipeline.
"""

import sys
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.api.routers.auth import require_recruiter_access
from src.parser.document_loader import (
    load_text_from_bytes,
    validate_resume_file,
    ensure_extractable_text,
    UnsupportedDocumentError,
)
from src.parser.resume_extractor import (
    extract_experience_years,
    extract_skills,
    extract_skills_semantic,
    redact_sensitive_information,
)
from src.storage import repository

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Postings & Applications"])


class JobCreateRequest(BaseModel):
    title: str
    description: str


class JobOutSchema(BaseModel):
    id: str
    title: str
    description: str
    created_at: str
    application_count: int = 0


class ApplicationOutSchema(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    declared_group: Optional[str] = None
    resume_raw_text: str
    resume_redacted_text: str
    skills: List[str]
    years_of_experience: Optional[float] = None
    submitted_at: str


class ApplicationSubmitResponse(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    declared_group: Optional[str] = None
    submitted_at: str


@router.post("", response_model=JobOutSchema, dependencies=[Depends(require_recruiter_access)])
def create_job(req: JobCreateRequest):
    """Recruiter creates a new job posting."""
    if not req.title.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Job title and description are required.")
    return repository.create_job(req.title.strip(), req.description.strip())


@router.get("", response_model=List[JobOutSchema])
def list_jobs_endpoint():
    """Public listing so Candidates can pick a job to apply to."""
    return repository.list_jobs()


@router.get("/{job_id}", response_model=JobOutSchema)
def get_job_endpoint(job_id: str):
    """Public job detail (Candidate apply page)."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    job["application_count"] = len(repository.list_applications(job_id))
    return job


@router.post("/{job_id}/applications", response_model=ApplicationSubmitResponse)
async def submit_application(
    job_id: str,
    candidate_name: str = Form(...),
    declared_group: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Candidate submits a CV against a job posting. Public, no access code."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    name = candidate_name.strip() or "Anonymous Candidate"
    try:
        content = await file.read()
        validate_resume_file(file.filename or "resume", content)
        text = load_text_from_bytes(content, file.filename or "resume.txt")
        ensure_extractable_text(text)
    except UnsupportedDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse resume file: {str(e)}")

    skills = set(extract_skills(text))
    try:
        skills |= set(extract_skills_semantic(text))
    except Exception as e:
        print(f"[jobs] semantic skill matching unavailable, falling back to regex: {e}", file=sys.stderr)
    skills = sorted(skills)
    years = extract_experience_years(text)
    redacted_text, _ = redact_sensitive_information(text, target_name=name)

    group_value = declared_group.strip() if declared_group and declared_group.strip() else None

    created = repository.create_application(
        job_id=job_id,
        candidate_name=name,
        declared_group=group_value,
        resume_raw_text=text,
        resume_redacted_text=redacted_text,
        skills=skills,
        years_of_experience=years,
    )
    return created


@router.get(
    "/{job_id}/applications",
    response_model=List[ApplicationOutSchema],
    dependencies=[Depends(require_recruiter_access)],
)
def list_applications_endpoint(job_id: str):
    """Recruiter-only: list every CV submitted for this job posting."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return repository.list_applications(job_id)
