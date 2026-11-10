"""Integration tests for FairRank-AI FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


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
