"""Integration tests for FairRank-AI FastAPI service."""

import io

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from src.api.main import app

client = TestClient(app)


def _pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_parse_text_endpoint():
    payload = {
        "text": "Candidate: Sarah McCarthy\nFrontend engineer with 3 years React and Docker experience."
    }
    res = client.post("/api/v1/ingestion/parse-text", data=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_name"] == "Sarah McCarthy"
    assert "React" in data["skills"]
    assert "Docker" in data["skills"]


def test_ranking_and_reranking_pipeline():
    payload = {
        "job_description": "Senior Python developer with Docker and FastAPI experience.",
        "candidates": [
            {
                "id": "c1",
                "name": "Lakisha Washington",
                "text": "Senior Python developer with 6 years experience in FastAPI and Docker.",
                "group": "Black Female",
                "relevance_grade": 2,
            },
            {
                "id": "c2",
                "name": "Brad Miller",
                "text": "Junior Python programmer with 1 year Docker exposure.",
                "group": "White Male",
                "relevance_grade": 1,
            },
            {
                "id": "c3",
                "name": "Claire Snyder",
                "text": "Financial accountant with Excel and QuickBooks experience.",
                "group": "White Female",
                "relevance_grade": 0,
            },
        ],
        "model_name": "bm25",
        "redaction_enabled": False,
        "lambda_penalty": 1.5,
        "cutoff_k": 3,
    }
    res = client.post("/api/v1/ranking/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["ranked_candidates"]) == 3
    assert data["ndcg_at_k"] > 0
    assert "black_white_exposure_gap" in data


def test_pareto_sweep_endpoint():
    payload = {
        "job_description": "Python engineer Docker",
        "candidates": [
            {
                "id": "c1",
                "name": "Jamal Washington",
                "text": "Python Docker microservices",
                "group": "Black Male",
                "relevance_grade": 2,
            },
            {
                "id": "c2",
                "name": "Emily Miller",
                "text": "Python Docker backend",
                "group": "White Female",
                "relevance_grade": 2,
            },
        ],
        "lambda_min": 0.0,
        "lambda_max": 2.0,
        "steps": 3,
        "cutoff_k": 2,
    }
    res = client.post("/api/v1/audit/pareto-sweep", json=payload)
    assert res.status_code == 200
    points = res.json()
    assert len(points) == 3
    assert points[0]["lambda_penalty"] == 0.0


def test_counterfactual_audit_endpoint():
    payload = {
        "job_description": "Lead Python Engineer",
        "candidate_profile": "Experienced software architect with 8 years building cloud microservices in Python.",
        "baseline_model": "bm25",
    }
    res = client.post("/api/v1/audit/counterfactual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["group_results"]) == 4
    assert "max_demographic_shift" in data


RECRUITER_HEADERS = {"X-Recruiter-Code": "fairrank-demo"}


def test_recruiter_login():
    res = client.post("/api/v1/auth/recruiter-login", json={"code": "fairrank-demo"})
    assert res.status_code == 200
    assert res.json()["ok"] is True

    bad = client.post("/api/v1/auth/recruiter-login", json={"code": "wrong-code"})
    assert bad.status_code == 401


def test_job_posting_and_application_flow():
    # Creating a job without the recruiter code is rejected.
    unauthorized = client.post(
        "/api/v1/jobs",
        json={"title": "QA Job", "description": "Should be rejected"},
    )
    assert unauthorized.status_code == 401

    create_res = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Engineer", "description": "Python, FastAPI, Docker."},
        headers=RECRUITER_HEADERS,
    )
    assert create_res.status_code == 200
    job = create_res.json()
    job_id = job["id"]

    # Public listing/detail should work without the recruiter code.
    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    assert any(j["id"] == job_id for j in list_res.json())

    detail_res = client.get(f"/api/v1/jobs/{job_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Backend Engineer"

    # Candidate submits an application (public endpoint).
    submit_res = client.post(
        f"/api/v1/jobs/{job_id}/applications",
        data={"candidate_name": "Jamal Washington", "declared_group": "Black_male"},
        files={"file": ("resume.txt", b"Senior backend engineer with FastAPI and Docker experience.", "text/plain")},
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["candidate_name"] == "Jamal Washington"

    # Listing applications requires the recruiter code.
    unauthorized_list = client.get(f"/api/v1/jobs/{job_id}/applications")
    assert unauthorized_list.status_code == 401

    applications_res = client.get(f"/api/v1/jobs/{job_id}/applications", headers=RECRUITER_HEADERS)
    assert applications_res.status_code == 200
    applications = applications_res.json()
    assert len(applications) == 1
    assert applications[0]["declared_group"] == "Black_male"

    # Verify PDF CV generation and streaming
    pdf_res = client.get(
        f"/api/v1/jobs/{job_id}/applications/{applications[0]['id']}/cv.pdf",
        headers=RECRUITER_HEADERS,
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # Verify PDF CV works with query parameter auth (?code=fairrank-demo)
    pdf_res_query = client.get(
        f"/api/v1/jobs/{job_id}/applications/{applications[0]['id']}/cv.pdf?code=fairrank-demo",
    )
    assert pdf_res_query.status_code == 200
    assert pdf_res_query.headers["content-type"] == "application/pdf"


def test_application_rejects_unsupported_file_type():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Reject Format Job", "description": "Testing upload validation."},
        headers=RECRUITER_HEADERS,
    ).json()

    res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Someone"},
        files={"file": ("resume.png", b"\x89PNG\r\n\x1a\n not a real png", "image/png")},
    )
    assert res.status_code == 400
    assert "định dạng" in res.json()["detail"].lower() or "format" in res.json()["detail"].lower()


def test_application_rejects_empty_file():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Reject Empty Job", "description": "Testing upload validation."},
        headers=RECRUITER_HEADERS,
    ).json()

    res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Someone"},
        files={"file": ("resume.txt", b"", "text/plain")},
    )
    assert res.status_code == 400


def test_application_rejects_unextractable_text():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Reject Blank Text Job", "description": "Testing upload validation."},
        headers=RECRUITER_HEADERS,
    ).json()

    # Below MIN_EXTRACTED_TEXT_CHARS — simulates a scanned/image-only PDF with no text layer.
    res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Someone"},
        files={"file": ("resume.txt", b"hi", "text/plain")},
    )
    assert res.status_code == 400
    assert "văn bản" in res.json()["detail"].lower()


def test_job_full_metadata_and_update():
    create_res = client.post(
        "/api/v1/jobs",
        json={
            "title": "Lead AI Architect",
            "description": "Architect scalable LLM and Fairness-aware recommendation systems.",
            "department": "AI Research",
            "location": "Remote / Danang",
            "employment_type": "Full-time",
            "experience_level": "Senior",
            "salary_min": 3500,
            "salary_max": 5500,
            "salary_currency": "USD",
            "status": "published",
            "requirements": ["PyTorch", "FastAPI", "Fairness Metrics", "Docker"],
        },
        headers=RECRUITER_HEADERS,
    )
    assert create_res.status_code == 200
    job = create_res.json()
    assert job["department"] == "AI Research"
    assert job["salary_max"] == 5500
    assert "PyTorch" in job["requirements"]

    # Update job
    update_res = client.patch(
        f"/api/v1/jobs/{job['id']}",
        json={"salary_max": 6000, "status": "published"},
        headers=RECRUITER_HEADERS,
    )
    assert update_res.status_code == 200
    assert update_res.json()["salary_max"] == 6000


def test_application_stage_transition_and_scorecard():
    # 1. Create Job
    job = client.post(
        "/api/v1/jobs",
        json={"title": "ML Engineer", "description": "Python, scikit-learn, PyTorch ML pipelines."},
        headers=RECRUITER_HEADERS,
    ).json()

    # 2. Submit application with extra contact fields
    submit_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={
            "candidate_name": "Tran Van A",
            "declared_group": "Asian_male",
            "email": "tran@example.com",
            "phone": "0987654321",
            "current_title": "Data Scientist",
            "location": "Hanoi",
        },
        files={"file": ("resume.txt", b"Experienced Data Scientist with 4 years in Python, PyTorch, and ML pipelines.", "text/plain")},
    )
    assert submit_res.status_code == 200
    app_id = submit_res.json()["id"]

    # 3. Move stage to 'shortlisted'
    stage_res = client.patch(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/stage",
        json={"stage": "shortlisted"},
        headers=RECRUITER_HEADERS,
    )
    assert stage_res.status_code == 200
    assert stage_res.json()["stage"] == "shortlisted"

    # 4. Submit Scorecard
    sc_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/scorecards",
        json={
            "evaluator_name": "Senior Interviewer",
            "overall_recommendation": "strong_hire",
            "technical_score": 5,
            "communication_score": 4,
            "experience_score": 5,
            "notes": "Excellent technical fundamentals and clear communication.",
        },
        headers=RECRUITER_HEADERS,
    )
    assert sc_res.status_code == 200
    assert sc_res.json()["overall_recommendation"] == "strong_hire"

    # 5. Verify Scorecards listing
    sc_list = client.get(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/scorecards",
        headers=RECRUITER_HEADERS,
    )
    assert sc_list.status_code == 200
    assert len(sc_list.json()) == 1


def test_interviews_and_email_simulation():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "DevOps Engineer", "description": "Docker, Kubernetes, CI/CD pipeline automation."},
        headers=RECRUITER_HEADERS,
    ).json()

    submit_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Le Thi B", "email": "le.thi@example.com"},
        files={"file": ("resume.txt", b"Senior DevOps Specialist with expertise in Docker, Kubernetes, and GitHub Actions.", "text/plain")},
    )
    app_id = submit_res.json()["id"]

    # Schedule interview
    intv_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/interviews",
        json={
            "round_type": "Technical Interview",
            "scheduled_at": "2026-11-20T10:00:00",
            "interviewer_name": "Head of Infrastructure",
            "meeting_link": "https://meet.google.com/test-link",
        },
        headers=RECRUITER_HEADERS,
    )
    assert intv_res.status_code == 200
    assert intv_res.json()["status"] == "scheduled"

    # Send email
    em_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/send-email",
        json={
            "template_type": "interview_invite",
            "recipient_email": "le.thi@example.com",
            "subject": "Interview Invitation",
            "body": "We invite you to interview for DevOps Engineer.",
        },
        headers=RECRUITER_HEADERS,
    )
    assert em_res.status_code == 200
    assert em_res.json()["status"] == "sent"


def test_talent_pool_and_analytics():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Product Designer", "description": "Figma, UI/UX prototyping, design systems."},
        headers=RECRUITER_HEADERS,
    ).json()

    client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Nguyen Designer", "declared_group": "White_female"},
        files={"file": ("resume.txt", b"Creative UI/UX Designer with 5 years experience in Figma, design systems, and wireframing.", "text/plain")},
    )

    # Search Talent Pool
    pool_res = client.get(
        "/api/v1/candidates?query=Designer",
        headers=RECRUITER_HEADERS,
    )
    assert pool_res.status_code == 200
    pool = pool_res.json()
    assert any(c["candidate_name"] == "Nguyen Designer" for c in pool)

    # Funnel Analytics
    analytics_res = client.get(
        f"/api/v1/jobs/{job['id']}/analytics",
        headers=RECRUITER_HEADERS,
    )
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert analytics["total_applications"] >= 1
    assert "stage_counts" in analytics


def test_run_fair_screening_and_advance_top():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Data Engineer", "description": "Spark, Kafka, SQL data warehouse pipelines."},
        headers=RECRUITER_HEADERS,
    ).json()

    # Submit 3 applications in 'new'
    for name, grp in [("Cand 1", "Black_female"), ("Cand 2", "White_male"), ("Cand 3", "Black_male")]:
        client.post(
            f"/api/v1/jobs/{job['id']}/applications",
            data={"candidate_name": name, "declared_group": grp},
            files={"file": ("resume.txt", f"Specialist in Spark, SQL, and Kafka pipelines with 5 years experience for {name}.".encode(), "text/plain")},
        )

    # Trigger run-fair-screening
    screen_res = client.post(
        f"/api/v1/jobs/{job['id']}/run-fair-screening",
        json={"lambda_penalty": 1.0, "target_stage": "screening", "from_stage": "new"},
        headers=RECRUITER_HEADERS,
    )
    assert screen_res.status_code == 200
    assert screen_res.json()["processed_count"] == 3

    # Check that they now appear in 'screening'
    screened_apps = client.get(
        f"/api/v1/jobs/{job['id']}/applications?stage=screening",
        headers=RECRUITER_HEADERS,
    ).json()
    assert len(screened_apps) == 3
    assert all(a["stage"] == "screening" for a in screened_apps)
    assert all(a["ai_score"] > 0 for a in screened_apps)

    # Advance candidates by candidate_ids
    cand_id_to_advance = screened_apps[0]["id"]
    adv_ids_res = client.post(
        f"/api/v1/jobs/{job['id']}/advance-top-candidates",
        json={"candidate_ids": [cand_id_to_advance], "target_stage": "shortlisted"},
        headers=RECRUITER_HEADERS,
    )
    assert adv_ids_res.status_code == 200
    assert adv_ids_res.json()["advanced_count"] == 1

    # Advance top candidates to shortlisted
    adv_res = client.post(
        f"/api/v1/jobs/{job['id']}/advance-top-candidates",
        json={"top_k": 2, "target_stage": "shortlisted"},
        headers=RECRUITER_HEADERS,
    )
    assert adv_res.status_code == 200
    assert adv_res.json()["advanced_count"] == 2


def test_job_ai_criteria_and_rescore():
    # 1. Create a job
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Fullstack AI Engineer", "description": "React, Python, FastAPI, Machine Learning."},
        headers=RECRUITER_HEADERS,
    ).json()

    # 2. Get initial criteria
    crit_res = client.get(f"/api/v1/jobs/{job['id']}/ai-criteria", headers=RECRUITER_HEADERS)
    assert crit_res.status_code == 200
    crit = crit_res.json()
    assert "must_have_skills" in crit

    # 3. Submit application
    app_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Nguyen AI Dev"},
        files={"file": ("resume.txt", b"Proficient in Python and FastAPI with 4 years experience. Familiar with React.", "text/plain")},
    ).json()

    # 4. Update AI criteria with custom must-have skills & re-score
    update_res = client.put(
        f"/api/v1/jobs/{job['id']}/ai-criteria?re_score=true",
        json={
            "must_have_skills": ["Python", "FastAPI", "React"],
            "nice_to_have_skills": ["Docker", "Kubernetes"],
            "min_experience_years": 3.0,
            "weight_keyword": 0.5,
            "weight_semantic": 0.3,
            "weight_experience": 0.2,
            "auto_advance_threshold": 75.0,
        },
        headers=RECRUITER_HEADERS,
    )
    assert update_res.status_code == 200
    assert update_res.json()["must_have_skills"] == ["Python", "FastAPI", "React"]

    # 5. Check application has updated AI score and matched/missing skills
    apps = client.get(f"/api/v1/jobs/{job['id']}/applications", headers=RECRUITER_HEADERS).json()
    assert len(apps) >= 1
    target_app = next(a for a in apps if a["id"] == app_res["id"])
    assert target_app["ai_score"] > 0
    assert "Python" in target_app["matched_skills"] or "Fastapi" in target_app["matched_skills"]
    assert "ai_rationale" in target_app and target_app["ai_rationale"]

    # 6. Call explicit re-score endpoint
    rescore_res = client.post(f"/api/v1/jobs/{job['id']}/re-score", headers=RECRUITER_HEADERS)
    assert rescore_res.status_code == 200
    assert rescore_res.json()["rescored_count"] >= 1


def test_job_with_no_criteria_does_not_score_against_unrelated_defaults():
    # A job with no requirements and no custom AI criteria set.
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Registered Nurse", "description": "Patient care in a busy hospital ward."},
        headers=RECRUITER_HEADERS,
    ).json()

    crit = client.get(f"/api/v1/jobs/{job['id']}/ai-criteria", headers=RECRUITER_HEADERS).json()
    # Must not silently default to unrelated frontend keywords.
    assert "React" not in crit["must_have_skills"]
    assert "TypeScript" not in crit["must_have_skills"]
    assert "Docker" not in crit["nice_to_have_skills"]

    app_res = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Nurse Candidate"},
        files={"file": ("resume.txt", b"5 years experience in patient care, wound dressing, and ward management.", "text/plain")},
    ).json()
    apps = client.get(f"/api/v1/jobs/{job['id']}/applications", headers=RECRUITER_HEADERS).json()
    target_app = next(a for a in apps if a["id"] == app_res["id"])
    # No must-have skills configured means nothing should show up as "missing".
    assert target_app["missing_skills"] == []


def test_candidates_router_detail_and_pdf_endpoints():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Platform Engineer", "description": "Kubernetes, Terraform, CI/CD pipelines."},
        headers=RECRUITER_HEADERS,
    ).json()

    submitted = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": "Talent Pool Candidate", "email": "tp-candidate@example.com"},
        files={"file": ("resume.txt", b"Platform engineer with Kubernetes and Terraform experience.", "text/plain")},
    ).json()
    app_id = submitted["id"]

    # Unauthorized access is rejected.
    assert client.get(f"/api/v1/candidates/{app_id}").status_code == 401

    detail_res = client.get(f"/api/v1/candidates/{app_id}", headers=RECRUITER_HEADERS)
    assert detail_res.status_code == 200
    assert detail_res.json()["candidate_name"] == "Talent Pool Candidate"

    assert client.get(f"/api/v1/candidates/does-not-exist", headers=RECRUITER_HEADERS).status_code == 404

    pdf_res = client.get(f"/api/v1/candidates/{app_id}/cv.pdf", headers=RECRUITER_HEADERS)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

    # The query-param auth exception applies to this PDF route too.
    pdf_res_query = client.get(f"/api/v1/candidates/{app_id}/cv.pdf?code=fairrank-demo")
    assert pdf_res_query.status_code == 200


def test_recruiter_access_rejects_wrong_or_missing_code():
    # Wrong header code on a standard recruiter-only endpoint.
    bad_header = client.get(
        "/api/v1/jobs/any-id/applications",
        headers={"X-Recruiter-Code": "totally-wrong"},
    )
    assert bad_header.status_code == 401

    # Missing code entirely.
    assert client.get("/api/v1/jobs/any-id/applications").status_code == 401

    # The general dependency does not accept a query-param code (only the PDF
    # routes do) — a correct code passed only as ?code= must still be rejected.
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Query Auth Probe", "description": "n/a"},
        headers=RECRUITER_HEADERS,
    ).json()
    query_only = client.get(f"/api/v1/jobs/{job['id']}/applications?code=fairrank-demo")
    assert query_only.status_code == 401


def test_blind_mode_cv_pdf_filename_never_leaks_candidate_name():
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Blind Screening Probe", "description": "Any role, testing blind CV rendering."},
        headers=RECRUITER_HEADERS,
    ).json()

    candidate_name = "Alexandra Identifiable Lastname"
    submitted = client.post(
        f"/api/v1/jobs/{job['id']}/applications",
        data={"candidate_name": candidate_name},
        files={"file": (
            "resume.txt",
            f"{candidate_name} is a software engineer with 6 years of experience in Python.".encode(),
            "text/plain",
        )},
    ).json()
    app_id = submitted["id"]

    blind_res = client.get(
        f"/api/v1/jobs/{job['id']}/applications/{app_id}/cv.pdf?blind=true",
        headers=RECRUITER_HEADERS,
    )
    assert blind_res.status_code == 200

    # The filename must be generic, never derived from the real candidate name,
    # regardless of how completely the resume body text was redacted.
    disposition = blind_res.headers.get("content-disposition", "")
    assert "filename=" in disposition
    assert candidate_name.split(" ")[0] not in disposition
    assert candidate_name.split(" ")[-1] not in disposition

    # The real name itself (redaction replaces it with [CANDIDATE_NAME]) must
    # not survive into the rendered PDF body.
    pdf_text = _pdf_text(blind_res.content)
    assert candidate_name not in pdf_text


def test_blind_mode_cv_pdf_never_falls_back_to_raw_text_when_redaction_is_empty():
    from src.storage.cv_pdf import generate_candidate_cv_pdf

    # Simulate an application whose redacted text is empty/missing — the bug
    # being guarded against is cv_pdf.py silently falling back to
    # resume_raw_text (fully unredacted, identifying content) in this case.
    app = {
        "candidate_name": "Should Not Appear Anywhere",
        "resume_raw_text": "Should Not Appear Anywhere, reachable at leak@example.com, 555-123-4567.",
        "resume_redacted_text": "",
        "skills": [],
    }
    pdf_bytes = generate_candidate_cv_pdf(app=app, job=None, blind_mode=True)
    pdf_text = _pdf_text(pdf_bytes)

    assert "Should Not Appear Anywhere" not in pdf_text
    assert "leak@example.com" not in pdf_text
    assert "555-123-4567" not in pdf_text



