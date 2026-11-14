"""Router for global Talent Pool management and cross-job candidate search."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from src.api.cv_streaming import build_cv_pdf_response
from src.api.routers.auth import require_recruiter_access, require_recruiter_access_pdf
from src.storage import repository

router = APIRouter(prefix="/api/v1/candidates", tags=["Central Talent Pool"])


@router.get("", dependencies=[Depends(require_recruiter_access)])
def search_talent_pool_endpoint(
    query: Optional[str] = None,
    skill: Optional[str] = None,
    min_exp: Optional[float] = None,
    stage: Optional[str] = None,
):
    """Searches candidates across all job postings in the central talent pool."""
    return repository.search_talent_pool(
        query=query,
        skill=skill,
        min_exp=min_exp,
        stage=stage,
    )


@router.get("/{app_id}", dependencies=[Depends(require_recruiter_access)])
def get_candidate_endpoint(app_id: str):
    """Retrieves full candidate profile across jobs."""
    app = repository.get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return app


@router.get("/{app_id}/cv.pdf", dependencies=[Depends(require_recruiter_access_pdf)])
def get_candidate_cv_pdf(app_id: str, blind: bool = False):
    """Streams the official PDF Curriculum Vitae for a candidate from the talent pool."""
    app = repository.get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    job = repository.get_job(app["job_id"]) if app.get("job_id") else None
    return build_cv_pdf_response(app=app, job=job, blind=blind)

