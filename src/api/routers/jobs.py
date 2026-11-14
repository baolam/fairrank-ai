"""Router for job postings, candidate applications, and full-featured enterprise ATS workflows."""

import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.api.cv_streaming import build_cv_pdf_response
from src.api.routers.auth import require_recruiter_access, require_recruiter_access_pdf
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
from src.models.bm25_ranker import BM25Ranker
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.mitigation import RerankerCandidateInput
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores

router = APIRouter(prefix="/api/v1/jobs", tags=["Job Postings & ATS Workflows"])
logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class JobCreateRequest(BaseModel):
    title: str
    description: str
    department: str = "Engineering"
    location: str = "Hybrid / Hanoi"
    employment_type: str = "Full-time"
    experience_level: str = "Mid-Level"
    salary_min: float = 0.0
    salary_max: float = 0.0
    salary_currency: str = "USD"
    status: str = "published"
    deadline: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[str] = None
    requirements: Optional[List[str]] = None


class AICriteriaSchema(BaseModel):
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = 1.0
    weight_semantic: float = 0.35
    weight_keyword: float = 0.45
    weight_experience: float = 0.20
    auto_advance_threshold: float = 70.0


class JobOutSchema(BaseModel):
    id: str
    title: str
    description: str
    created_at: str
    department: Optional[str] = "Engineering"
    location: Optional[str] = "Hybrid / Hanoi"
    employment_type: Optional[str] = "Full-time"
    experience_level: Optional[str] = "Mid-Level"
    salary_min: Optional[float] = 0.0
    salary_max: Optional[float] = 0.0
    salary_currency: Optional[str] = "USD"
    status: Optional[str] = "published"
    deadline: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    ai_criteria: Optional[AICriteriaSchema] = None
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
    email: Optional[str] = ""
    phone: Optional[str] = ""
    current_title: Optional[str] = ""
    location: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    stage: Optional[str] = "new"
    rejection_reason: Optional[str] = ""
    overall_rating: Optional[float] = 0.0
    ai_score: Optional[float] = 0.0
    ai_rationale: Optional[str] = ""
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)


class ApplicationSubmitResponse(BaseModel):
    id: str
    job_id: str
    candidate_name: str
    declared_group: Optional[str] = None
    submitted_at: str
    stage: str = "new"
    ai_score: float = 0.0


class StageUpdateRequest(BaseModel):
    stage: str
    rejection_reason: Optional[str] = None


class RatingUpdateRequest(BaseModel):
    rating: float


class ScorecardCreateRequest(BaseModel):
    evaluator_name: str
    overall_recommendation: str
    technical_score: int = Field(default=3, ge=1, le=5)
    communication_score: int = Field(default=3, ge=1, le=5)
    experience_score: int = Field(default=3, ge=1, le=5)
    notes: str = ""


class NoteCreateRequest(BaseModel):
    author_name: str
    content: str


class InterviewCreateRequest(BaseModel):
    round_type: str
    scheduled_at: str
    interviewer_name: str
    duration_minutes: int = 45
    meeting_link: str = ""
    location: str = "Online"
    notes: str = ""


class InterviewStatusUpdateRequest(BaseModel):
    status: str


class EmailSendRequest(BaseModel):
    template_type: str
    recipient_email: str
    subject: str
    body: str


# ==============================================================================
# Job Postings Endpoints
# ==============================================================================

@router.post("", response_model=JobOutSchema, dependencies=[Depends(require_recruiter_access)])
def create_job(req: JobCreateRequest):
    """Recruiter creates a new job posting with rich enterprise metadata."""
    if not req.title.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Job title and description are required.")
    return repository.create_job(
        title=req.title.strip(),
        description=req.description.strip(),
        department=req.department,
        location=req.location,
        employment_type=req.employment_type,
        experience_level=req.experience_level,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        salary_currency=req.salary_currency,
        status=req.status,
        deadline=req.deadline,
        requirements=req.requirements,
    )


@router.get("", response_model=List[JobOutSchema])
def list_jobs_endpoint(
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
):
    """Listing with optional status, department, and search filter."""
    return repository.list_jobs(status=status, department=department, search=search)


@router.get("/email-templates")
def get_email_templates_endpoint():
    """Returns available email templates for candidate communication."""
    return repository.EMAIL_TEMPLATES


@router.get("/{job_id}", response_model=JobOutSchema)
def get_job_endpoint(job_id: str):
    """Public job detail."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return job


@router.patch("/{job_id}", response_model=JobOutSchema, dependencies=[Depends(require_recruiter_access)])
def update_job_endpoint(job_id: str, req: JobUpdateRequest):
    """Recruiter updates job posting metadata or status."""
    updated = repository.update_job(
        job_id=job_id,
        title=req.title,
        description=req.description,
        department=req.department,
        location=req.location,
        employment_type=req.employment_type,
        experience_level=req.experience_level,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        salary_currency=req.salary_currency,
        status=req.status,
        deadline=req.deadline,
        requirements=req.requirements,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return updated


@router.delete("/{job_id}", dependencies=[Depends(require_recruiter_access)])
def delete_job_endpoint(job_id: str):
    """Recruiter deletes a job posting and its associated applications."""
    success = repository.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return {"ok": True, "deleted_job_id": job_id}


# ==============================================================================
# Candidate Application Submission & AI Scoring
# ==============================================================================

@router.post("/{job_id}/applications", response_model=ApplicationSubmitResponse)
async def submit_application(
    job_id: str,
    candidate_name: str = Form(...),
    declared_group: Optional[str] = Form(None),
    email: Optional[str] = Form(""),
    phone: Optional[str] = Form(""),
    current_title: Optional[str] = Form(""),
    location: Optional[str] = Form(""),
    linkedin_url: Optional[str] = Form(""),
    file: UploadFile = File(...),
):
    """Candidate submits a CV against a job posting. Automatically triggers parsing & AI match scoring."""
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
        logger.warning("Semantic skill matching unavailable, falling back to regex: %s", e)
    skills = sorted(skills)
    years = extract_experience_years(text)
    redacted_text, _ = redact_sensitive_information(text, target_name=name)

    group_value = declared_group.strip() if declared_group and declared_group.strip() else None

    # Calculate AI Match score and keyword matching using job's AI criteria
    criteria = job.get("ai_criteria") or {}
    match_info = repository.calculate_candidate_match(
        job_description=job["description"],
        ai_criteria=criteria,
        candidate_text=text,
        candidate_skills=skills,
        candidate_years=years,
    )
    ai_score = match_info.get("ai_score", 65.0)
    ai_rationale = match_info.get("ai_rationale", "")
    matched_skills = match_info.get("matched_skills", [])
    missing_skills = match_info.get("missing_skills", [])

    try:
        created = repository.create_application(
            job_id=job_id,
            candidate_name=name,
            declared_group=group_value,
            resume_raw_text=text,
            resume_redacted_text=redacted_text,
            skills=skills,
            years_of_experience=years,
            email=email or "",
            phone=phone or "",
            current_title=current_title or "",
            location=location or "",
            linkedin_url=linkedin_url or "",
            stage="new",
            ai_score=ai_score,
            ai_rationale=ai_rationale,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )
    except repository.DuplicateApplicationError:
        raise HTTPException(
            status_code=409,
            detail="An application from this email already exists for this job posting.",
        )

    if content.startswith(b"%PDF"):
        try:
            resumes_dir = Path("data") / "resumes"
            resumes_dir.mkdir(parents=True, exist_ok=True)
            with open(resumes_dir / f"{created['id']}.pdf", "wb") as f:
                f.write(content)
        except Exception as e:
            logger.warning("Failed to save uploaded PDF for application %s: %s", created["id"], e)

    return created


@router.get(
    "/{job_id}/applications",
    response_model=List[ApplicationOutSchema],
    dependencies=[Depends(require_recruiter_access)],
)
def list_applications_endpoint(
    job_id: str,
    stage: Optional[str] = None,
    search: Optional[str] = None,
):
    """Recruiter-only: list applications submitted for this job posting with optional stage filter."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return repository.list_applications(job_id, stage=stage, search=search)


@router.get(
    "/{job_id}/applications/{app_id}",
    response_model=ApplicationOutSchema,
    dependencies=[Depends(require_recruiter_access)],
)
def get_application_endpoint(job_id: str, app_id: str):
    """Recruiter-only: inspect full application details."""
    app = repository.get_application(app_id)
    if not app or app["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="Application not found.")
    return app


@router.get(
    "/{job_id}/applications/{app_id}/cv.pdf",
    dependencies=[Depends(require_recruiter_access_pdf)],
)
def get_application_cv_pdf(job_id: str, app_id: str, blind: bool = False):
    """Streams the official PDF Curriculum Vitae for a candidate application."""
    app = repository.get_application(app_id)
    if not app or app["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="Application not found.")
    job = repository.get_job(job_id)
    return build_cv_pdf_response(app=app, job=job, blind=blind)


@router.patch(
    "/{job_id}/applications/{app_id}/stage",
    response_model=ApplicationOutSchema,
    dependencies=[Depends(require_recruiter_access)],
)
def update_stage_endpoint(job_id: str, app_id: str, req: StageUpdateRequest):
    """Move candidate across Kanban pipeline stages."""
    app = repository.get_application(app_id)
    if not app or app["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="Application not found.")
    updated = repository.update_application_stage(app_id, req.stage, req.rejection_reason)
    return updated


@router.patch(
    "/{job_id}/applications/{app_id}/rating",
    response_model=ApplicationOutSchema,
    dependencies=[Depends(require_recruiter_access)],
)
def update_rating_endpoint(job_id: str, app_id: str, req: RatingUpdateRequest):
    """Update overall candidate rating."""
    updated = repository.update_application_rating(app_id, req.rating)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found.")
    return updated


# ==============================================================================
# Scorecards, Notes, Interviews, and Emails Endpoints
# ==============================================================================

@router.post("/{job_id}/applications/{app_id}/scorecards", dependencies=[Depends(require_recruiter_access)])
def create_scorecard_endpoint(job_id: str, app_id: str, req: ScorecardCreateRequest):
    """Submits candidate interview scorecard."""
    return repository.create_scorecard(
        application_id=app_id,
        evaluator_name=req.evaluator_name,
        overall_recommendation=req.overall_recommendation,
        technical_score=req.technical_score,
        communication_score=req.communication_score,
        experience_score=req.experience_score,
        notes=req.notes,
    )


@router.get("/{job_id}/applications/{app_id}/scorecards", dependencies=[Depends(require_recruiter_access)])
def list_scorecards_endpoint(job_id: str, app_id: str):
    """Lists scorecards submitted for this candidate."""
    return repository.list_scorecards(app_id)


@router.post("/{job_id}/applications/{app_id}/notes", dependencies=[Depends(require_recruiter_access)])
def create_note_endpoint(job_id: str, app_id: str, req: NoteCreateRequest):
    """Adds a recruiter collaboration note to candidate profile."""
    return repository.create_note(app_id, req.author_name, req.content)


@router.get("/{job_id}/applications/{app_id}/notes", dependencies=[Depends(require_recruiter_access)])
def list_notes_endpoint(job_id: str, app_id: str):
    """Retrieves recruiter notes for candidate."""
    return repository.list_notes(app_id)


@router.post("/{job_id}/applications/{app_id}/interviews", dependencies=[Depends(require_recruiter_access)])
def schedule_interview_endpoint(job_id: str, app_id: str, req: InterviewCreateRequest):
    """Schedules an interview round for candidate."""
    return repository.create_interview(
        application_id=app_id,
        round_type=req.round_type,
        scheduled_at=req.scheduled_at,
        interviewer_name=req.interviewer_name,
        duration_minutes=req.duration_minutes,
        meeting_link=req.meeting_link,
        location=req.location,
        notes=req.notes,
    )


@router.get("/{job_id}/applications/{app_id}/interviews", dependencies=[Depends(require_recruiter_access)])
def list_candidate_interviews_endpoint(job_id: str, app_id: str):
    """Lists interview rounds scheduled for candidate."""
    return repository.list_interviews(application_id=app_id)


@router.get("/{job_id}/interviews", dependencies=[Depends(require_recruiter_access)])
def list_job_interviews_endpoint(job_id: str):
    """Lists all upcoming interviews across all applicants of this job."""
    return repository.list_interviews(job_id=job_id)


@router.patch("/{job_id}/interviews/{interview_id}", dependencies=[Depends(require_recruiter_access)])
def update_interview_status_endpoint(job_id: str, interview_id: str, req: InterviewStatusUpdateRequest):
    """Updates interview status ('completed', 'cancelled', 'scheduled')."""
    res = repository.update_interview_status(interview_id, req.status)
    if not res:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return res


@router.post("/{job_id}/applications/{app_id}/send-email", dependencies=[Depends(require_recruiter_access)])
def send_email_endpoint(job_id: str, app_id: str, req: EmailSendRequest):
    """Simulates sending an email to candidate and logs it."""
    return repository.create_email_log(
        application_id=app_id,
        recipient_email=req.recipient_email,
        template_type=req.template_type,
        subject=req.subject,
        body=req.body,
    )


@router.get("/{job_id}/applications/{app_id}/emails", dependencies=[Depends(require_recruiter_access)])
def list_emails_endpoint(job_id: str, app_id: str):
    """Retrieves email logs for candidate."""
    return repository.list_email_logs(app_id)


# ==============================================================================
# ATS Funnel Analytics & Adverse Impact (4/5ths Rule)
# ==============================================================================

@router.get("/{job_id}/analytics", dependencies=[Depends(require_recruiter_access)])
def get_job_analytics_endpoint(job_id: str):
    """Returns funnel metrics, stage counts, and EEOC Adverse Impact ratios."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return repository.get_job_funnel_analytics(job_id)


class RunFairScreeningRequest(BaseModel):
    model_name: str = "bm25"
    redaction_enabled: bool = False
    lambda_penalty: float = 1.0
    cutoff_k: int = 10
    target_stage: str = "screening"
    from_stage: Optional[str] = None


@router.post("/{job_id}/run-fair-screening", dependencies=[Depends(require_recruiter_access)])
def run_fair_screening_endpoint(job_id: str, req: RunFairScreeningRequest = RunFairScreeningRequest()):
    """Executes Fair AI Ranking on candidate applications for this job and moves them to target_stage (default 'screening')."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    all_apps = repository.list_applications(job_id)
    if not all_apps:
        return {"processed_count": 0, "message": "Chưa có hồ sơ ứng viên nào trong job này."}

    # Filter target applications to screen
    target_apps = [
        a for a in all_apps
        if req.from_stage is None or a.get("stage") == req.from_stage or req.from_stage == "all"
    ]
    if not target_apps:
        target_apps = all_apps

    # 1. Prepare texts
    processed_texts = []
    for a in target_apps:
        if req.redaction_enabled:
            processed_texts.append(a.get("resume_redacted_text") or a.get("resume_raw_text", ""))
        else:
            processed_texts.append(f"Candidate: {a['candidate_name']}\n\n{a.get('resume_raw_text', '')}")

    # 2. Score candidates
    if req.model_name.lower() == "sbert":
        try:
            from src.api.dependencies import get_sbert_ranker
            scorer = get_sbert_ranker()
            raw_scores = scorer.score_candidates(job["description"], processed_texts)
        except Exception:
            scorer = BM25Ranker()
            raw_scores = scorer.score_candidates(job["description"], processed_texts)
    else:
        scorer = BM25Ranker()
        raw_scores = scorer.score_candidates(job["description"], processed_texts)

    norm_scores = compute_min_max_normalized_scores(raw_scores)

    # 3. Optional Greedy Fair Reranking
    # Candidates without a declared group are distributed round-robin across all
    # groups rather than defaulting to one group, which would bias that group's
    # exposure bookkeeping (same pattern used in JobApplicationsStep/UploadDataStep).
    all_groups = list(IntersectionalGroup)
    reranker_inputs = [
        RerankerCandidateInput(
            variant_id=a["id"],
            base_resume_id=a["id"],
            group=IntersectionalGroup(a["declared_group"]) if a.get("declared_group") in [g.value for g in IntersectionalGroup] else all_groups[i % len(all_groups)],
            frozen_score=raw_scores[i],
            normalized_score=norm_scores[i],
            relevance_grade=2 if norm_scores[i] >= 0.7 else (1 if norm_scores[i] >= 0.4 else 0),
            tie_breaker_id=a["id"],
        )
        for i, a in enumerate(target_apps)
    ]

    reranked = run_greedy_exposure_reranking(
        candidates=reranker_inputs,
        lambda_penalty=req.lambda_penalty,
        cutoff_k=req.cutoff_k,
    )

    # 4. Map updated scores and update stages in repository
    import numpy as np
    criteria = job.get("ai_criteria") or {}
    scores_map = {}
    for r in reranked:
        pct_score = round(max(25.0, float(r.normalized_score) * 100.0), 1)
        exposure_val = 1.0 / np.log2(r.reranked_rank + 1) if r.reranked_rank <= req.cutoff_k else 0.0
        app_obj = next((a for a in target_apps if a["id"] == r.base_resume_id), None)
        matched_s = []
        missing_s = []
        if app_obj:
            match_res = repository.calculate_candidate_match(
                job_description=job["description"],
                ai_criteria=criteria,
                candidate_text=app_obj.get("resume_raw_text", ""),
                candidate_skills=app_obj.get("skills", []),
                candidate_years=app_obj.get("years_of_experience"),
            )
            matched_s = match_res.get("matched_skills", [])
            missing_s = match_res.get("missing_skills", [])
        missing_note = f" (thiếu {len(missing_s)} kỹ năng)" if missing_s else " (đủ kỹ năng bắt buộc)"
        rationale = f"Fair AI Rank #{r.reranked_rank} (Exposure: {round(float(exposure_val), 3)} | Match Score: {pct_score}%){missing_note}"
        scores_map[r.base_resume_id] = (pct_score, rationale, matched_s, missing_s)

    target_app_ids = [a["id"] for a in target_apps]
    repository.bulk_update_application_stages(target_app_ids, req.target_stage)
    repository.bulk_update_ai_scores(scores_map)

    return {
        "processed_count": len(target_apps),
        "target_stage": req.target_stage,
        "message": f"Đã sàng lọc và xếp hạng công bằng thành công {len(target_apps)} hồ sơ vào cột '{req.target_stage}'.",
    }


class AdvanceTopRequest(BaseModel):
    top_k: Optional[int] = None
    min_score: Optional[float] = None
    candidate_ids: Optional[List[str]] = None
    target_stage: str = "shortlisted"
    from_stage: str = "screening"


@router.post("/{job_id}/advance-top-candidates", dependencies=[Depends(require_recruiter_access)])
def advance_top_candidates_endpoint(job_id: str, req: AdvanceTopRequest = AdvanceTopRequest()):
    """Advances chosen, threshold-satisfying, or top K candidates into target_stage (default 'shortlisted')."""
    if req.candidate_ids:
        count = repository.bulk_update_application_stages(req.candidate_ids, req.target_stage)
        return {"advanced_count": count, "target_stage": req.target_stage}

    apps = repository.list_applications(job_id, stage=req.from_stage)
    if not apps:
        apps = repository.list_applications(job_id)

    if req.min_score is not None:
        qualifying = [a for a in apps if (a.get("ai_score") or 0.0) >= req.min_score]
        app_ids = [a["id"] for a in qualifying]
    elif req.top_k is not None:
        sorted_apps = sorted(apps, key=lambda a: a.get("ai_score") or 0.0, reverse=True)
        top_candidates = sorted_apps[:req.top_k]
        app_ids = [a["id"] for a in top_candidates]
    else:
        sorted_apps = sorted(apps, key=lambda a: a.get("ai_score") or 0.0, reverse=True)
        top_candidates = sorted_apps[:10]
        app_ids = [a["id"] for a in top_candidates]

    count = repository.bulk_update_application_stages(app_ids, req.target_stage)
    return {"advanced_count": count, "target_stage": req.target_stage}


class AICriteriaUpdateRequest(BaseModel):
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = Field(default=1.0, ge=0.0)
    weight_semantic: float = Field(default=0.35, ge=0.0, le=1.0)
    weight_keyword: float = Field(default=0.45, ge=0.0, le=1.0)
    weight_experience: float = Field(default=0.20, ge=0.0, le=1.0)
    auto_advance_threshold: float = Field(default=70.0, ge=0.0, le=100.0)


@router.get("/{job_id}/ai-criteria", response_model=AICriteriaSchema, dependencies=[Depends(require_recruiter_access)])
def get_job_ai_criteria_endpoint(job_id: str):
    """Retrieve the AI & Keyword matching setup for a specific job."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return job.get("ai_criteria") or {}


@router.put("/{job_id}/ai-criteria", response_model=AICriteriaSchema, dependencies=[Depends(require_recruiter_access)])
def update_job_ai_criteria_endpoint(
    job_id: str,
    req: AICriteriaUpdateRequest,
    re_score: bool = True,
):
    """Update AI and keyword criteria for a job and optionally re-score all applications."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    criteria_dict = req.model_dump()
    updated = repository.update_job_ai_criteria(job_id, criteria_dict)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update AI criteria.")

    if re_score:
        repository.re_score_job_applications(job_id)

    return updated.get("ai_criteria") or {}


@router.post("/{job_id}/re-score", dependencies=[Depends(require_recruiter_access)])
def rescore_job_applications_endpoint(job_id: str):
    """Re-scores all applications for this job against current AI & Keyword criteria."""
    job = repository.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    rescored = repository.re_score_job_applications(job_id)
    return {
        "job_id": job_id,
        "rescored_count": len(rescored),
        "message": f"Đã tính toán và cập nhật lại điểm AI cho {len(rescored)} hồ sơ thành công.",
    }


