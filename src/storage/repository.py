"""CRUD operations for job postings, candidate applications, and enterprise ATS records."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.storage.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DuplicateApplicationError(Exception):
    """Raised when a candidate with a known email re-submits to a job they already applied to."""

    def __init__(self, job_id: str, email: str):
        self.job_id = job_id
        self.email = email
        super().__init__(f"An application from '{email}' already exists for job '{job_id}'.")


# ==============================================================================
# Job Postings CRUD
# ==============================================================================

def create_job(
    title: str,
    description: str,
    department: str = "Engineering",
    location: str = "Hybrid / Hanoi",
    employment_type: str = "Full-time",
    experience_level: str = "Mid-Level",
    salary_min: float = 0.0,
    salary_max: float = 0.0,
    salary_currency: str = "USD",
    status: str = "published",
    deadline: Optional[str] = None,
    requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    created_at = _now()
    reqs_json = json.dumps(requirements or [])
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
                id, title, description, created_at, department, location,
                employment_type, experience_level, salary_min, salary_max,
                salary_currency, status, deadline, requirements_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                title,
                description,
                created_at,
                department,
                location,
                employment_type,
                experience_level,
                salary_min,
                salary_max,
                salary_currency,
                status,
                deadline,
                reqs_json,
            ),
        )
        conn.commit()

    return {
        "id": job_id,
        "title": title,
        "description": description,
        "created_at": created_at,
        "department": department,
        "location": location,
        "employment_type": employment_type,
        "experience_level": experience_level,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "status": status,
        "deadline": deadline,
        "requirements": requirements or [],
        "application_count": 0,
    }


def update_job(
    job_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    salary_min: Optional[float] = None,
    salary_max: Optional[float] = None,
    salary_currency: Optional[str] = None,
    status: Optional[str] = None,
    deadline: Optional[str] = None,
    requirements: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    current = get_job(job_id)
    if not current:
        return None

    new_title = title if title is not None else current["title"]
    new_desc = description if description is not None else current["description"]
    new_dept = department if department is not None else current.get("department", "Engineering")
    new_loc = location if location is not None else current.get("location", "Hybrid / Hanoi")
    new_type = employment_type if employment_type is not None else current.get("employment_type", "Full-time")
    new_level = experience_level if experience_level is not None else current.get("experience_level", "Mid-Level")
    new_smin = salary_min if salary_min is not None else current.get("salary_min", 0.0)
    new_smax = salary_max if salary_max is not None else current.get("salary_max", 0.0)
    new_curr = salary_currency if salary_currency is not None else current.get("salary_currency", "USD")
    new_stat = status if status is not None else current.get("status", "published")
    new_dead = deadline if deadline is not None else current.get("deadline")
    new_reqs = requirements if requirements is not None else current.get("requirements", [])

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE jobs SET
                title = ?, description = ?, department = ?, location = ?,
                employment_type = ?, experience_level = ?, salary_min = ?,
                salary_max = ?, salary_currency = ?, status = ?, deadline = ?,
                requirements_json = ?
            WHERE id = ?
            """,
            (
                new_title,
                new_desc,
                new_dept,
                new_loc,
                new_type,
                new_level,
                new_smin,
                new_smax,
                new_curr,
                new_stat,
                new_dead,
                json.dumps(new_reqs),
                job_id,
            ),
        )
        conn.commit()

    return get_job(job_id)


def _format_job_item(item: Dict[str, Any]) -> Dict[str, Any]:
    reqs = item.pop("requirements_json", None)
    item["requirements"] = json.loads(reqs) if reqs else []
    crit_raw = item.pop("ai_criteria_json", None)
    reqs_list = item["requirements"]
    if crit_raw and crit_raw != "{}" and crit_raw != "":
        try:
            item["ai_criteria"] = json.loads(crit_raw)
        except Exception:
            item["ai_criteria"] = {}
    else:
        item["ai_criteria"] = {}

    if not item["ai_criteria"]:
        # No custom AI criteria configured: derive must/nice-to-have skills only
        # from this job's own requirements, never from unrelated hardcoded
        # defaults — calculate_candidate_match() treats an empty skill list as
        # "no keyword requirement" rather than scoring against junk keywords.
        item["ai_criteria"] = {
            "must_have_skills": reqs_list[:3] if reqs_list else [],
            "nice_to_have_skills": reqs_list[3:] if len(reqs_list) > 3 else [],
            "min_experience_years": 3.0 if "senior" in item.get("title", "").lower() else 1.0,
            "weight_semantic": 0.35,
            "weight_keyword": 0.45,
            "weight_experience": 0.20,
            "auto_advance_threshold": 70.0,
        }
    return item


def list_jobs(
    status: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = """
        SELECT j.*, COUNT(a.id) AS application_count
        FROM jobs j
        LEFT JOIN applications a ON a.job_id = j.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND j.status = ?"
        params.append(status)
    if department:
        query += " AND j.department = ?"
        params.append(department)
    if search:
        query += " AND (j.title LIKE ? OR j.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " GROUP BY j.id ORDER BY j.created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    return [_format_job_item(dict(row)) for row in rows]


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT j.*, COUNT(a.id) AS application_count
            FROM jobs j
            LEFT JOIN applications a ON a.job_id = j.id
            WHERE j.id = ?
            GROUP BY j.id
            """,
            (job_id,),
        ).fetchone()
    if not row:
        return None
    return _format_job_item(dict(row))


def update_job_ai_criteria(job_id: str, ai_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET ai_criteria_json = ? WHERE id = ?",
            (json.dumps(ai_criteria), job_id),
        )
        conn.commit()
    return get_job(job_id)


def delete_job(job_id: str) -> bool:
    with get_connection() as conn:
        app_ids = [row["id"] for row in conn.execute(
            "SELECT id FROM applications WHERE job_id = ?", (job_id,)
        ).fetchall()]
        if app_ids:
            placeholders = ",".join("?" for _ in app_ids)
            # Child records must go before their parent application rows now
            # that PRAGMA foreign_keys is enforced.
            conn.execute(f"DELETE FROM scorecards WHERE application_id IN ({placeholders})", app_ids)
            conn.execute(f"DELETE FROM recruiter_notes WHERE application_id IN ({placeholders})", app_ids)
            conn.execute(f"DELETE FROM interviews WHERE application_id IN ({placeholders})", app_ids)
            conn.execute(f"DELETE FROM email_logs WHERE application_id IN ({placeholders})", app_ids)
        conn.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
        cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
    return cursor.rowcount > 0


# ==============================================================================
# Applications & Candidate Ingestion CRUD
# ==============================================================================

def create_application(
    job_id: str,
    candidate_name: str,
    declared_group: Optional[str],
    resume_raw_text: str,
    resume_redacted_text: str,
    skills: List[str],
    years_of_experience: Optional[float],
    email: str = "",
    phone: str = "",
    current_title: str = "",
    location: str = "",
    linkedin_url: str = "",
    stage: str = "new",
    ai_score: float = 0.0,
    ai_rationale: str = "",
    matched_skills: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    app_id = f"app_{uuid.uuid4().hex[:10]}"
    submitted_at = _now()
    matched_json = json.dumps(matched_skills or [])
    missing_json = json.dumps(missing_skills or [])
    with get_connection() as conn:
        # Anonymous applicants (blank email) are never deduplicated this way.
        if email:
            existing = conn.execute(
                "SELECT id FROM applications WHERE job_id = ? AND email = ? COLLATE NOCASE",
                (job_id, email),
            ).fetchone()
            if existing:
                raise DuplicateApplicationError(job_id, email)

        conn.execute(
            """
            INSERT INTO applications (
                id, job_id, candidate_name, declared_group, resume_raw_text,
                resume_redacted_text, skills_json, years_of_experience, submitted_at,
                email, phone, current_title, location, linkedin_url, stage,
                rejection_reason, overall_rating, ai_score, ai_rationale,
                matched_skills_json, missing_skills_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                email,
                phone,
                current_title,
                location,
                linkedin_url,
                stage,
                "",
                0.0,
                ai_score,
                ai_rationale,
                matched_json,
                missing_json,
            ),
        )
        conn.commit()

    return {
        "id": app_id,
        "job_id": job_id,
        "candidate_name": candidate_name,
        "declared_group": declared_group,
        "submitted_at": submitted_at,
        "email": email,
        "phone": phone,
        "current_title": current_title,
        "location": location,
        "linkedin_url": linkedin_url,
        "stage": stage,
        "ai_score": ai_score,
        "ai_rationale": ai_rationale,
        "matched_skills": matched_skills or [],
        "missing_skills": missing_skills or [],
    }


def _format_app_item(item: Dict[str, Any]) -> Dict[str, Any]:
    item["skills"] = json.loads(item.pop("skills_json", "[]"))
    m_raw = item.pop("matched_skills_json", None)
    item["matched_skills"] = json.loads(m_raw) if m_raw else []
    mis_raw = item.pop("missing_skills_json", None)
    item["missing_skills"] = json.loads(mis_raw) if mis_raw else []
    return item


def list_applications(
    job_id: str,
    stage: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM applications WHERE job_id = ?"
    params = [job_id]
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    if search:
        query += " AND (candidate_name LIKE ? OR current_title LIKE ? OR skills_json LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY submitted_at ASC"

    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    return [_format_app_item(dict(row)) for row in rows]


def get_application(app_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not row:
        return None
    return _format_app_item(dict(row))


def update_application_stage(
    app_id: str,
    stage: str,
    rejection_reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE applications
            SET stage = ?, rejection_reason = COALESCE(?, rejection_reason)
            WHERE id = ?
            """,
            (stage, rejection_reason, app_id),
        )
        conn.commit()
    return get_application(app_id)


def update_application_rating(app_id: str, rating: float) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE applications SET overall_rating = ? WHERE id = ?",
            (rating, app_id),
        )
        conn.commit()
    return get_application(app_id)


def update_application_ai_score(app_id: str, ai_score: float, ai_rationale: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE applications SET ai_score = ?, ai_rationale = ? WHERE id = ?",
            (ai_score, ai_rationale, app_id),
        )
        conn.commit()


def bulk_update_application_stages(app_ids: List[str], stage: str) -> int:
    if not app_ids:
        return 0
    with get_connection() as conn:
        placeholders = ",".join("?" for _ in app_ids)
        cursor = conn.execute(
            f"UPDATE applications SET stage = ? WHERE id IN ({placeholders})",
            (stage, *app_ids),
        )
        conn.commit()
    return cursor.rowcount


def bulk_update_ai_scores(scores_map: Dict[str, Any]) -> None:
    if not scores_map:
        return
    with get_connection() as conn:
        for app_id, data in scores_map.items():
            if isinstance(data, dict):
                score = data.get("ai_score", 0.0)
                rationale = data.get("ai_rationale", "")
                matched = json.dumps(data.get("matched_skills", []))
                missing = json.dumps(data.get("missing_skills", []))
            elif isinstance(data, (tuple, list)):
                score = data[0]
                rationale = data[1] if len(data) > 1 else ""
                matched = json.dumps(data[2]) if len(data) > 2 else "[]"
                missing = json.dumps(data[3]) if len(data) > 3 else "[]"
            else:
                score = float(data)
                rationale = ""
                matched = "[]"
                missing = "[]"
            conn.execute(
                """
                UPDATE applications
                SET ai_score = ?, ai_rationale = ?, matched_skills_json = ?, missing_skills_json = ?
                WHERE id = ?
                """,
                (score, rationale, matched, missing, app_id),
            )
        conn.commit()


def calculate_candidate_match(
    job_description: str,
    ai_criteria: Dict[str, Any],
    candidate_text: str,
    candidate_skills: List[str],
    candidate_years: Optional[float],
) -> Dict[str, Any]:
    from src.models.bm25_ranker import BM25Ranker

    must_haves = [s.strip().lower() for s in ai_criteria.get("must_have_skills", []) if s.strip()]
    nice_to_haves = [s.strip().lower() for s in ai_criteria.get("nice_to_have_skills", []) if s.strip()]
    min_exp = float(ai_criteria.get("min_experience_years", 1.0))
    w_sem = float(ai_criteria.get("weight_semantic", 0.35))
    w_key = float(ai_criteria.get("weight_keyword", 0.45))
    w_exp = float(ai_criteria.get("weight_experience", 0.20))

    cand_skills_lower = {s.lower() for s in candidate_skills}
    text_lower = candidate_text.lower()

    # Must-have skills matching
    matched_must = []
    missing_must = []
    for skill in must_haves:
        if skill in cand_skills_lower or skill in text_lower:
            matched_must.append(skill.title())
        else:
            missing_must.append(skill.title())

    # Nice-to-have skills matching
    matched_nice = []
    for skill in nice_to_haves:
        if skill in cand_skills_lower or skill in text_lower:
            matched_nice.append(skill.title())

    must_ratio = len(matched_must) / len(must_haves) if must_haves else 1.0
    nice_ratio = len(matched_nice) / len(nice_to_haves) if nice_to_haves else 1.0
    keyword_score = (must_ratio * 0.7 + nice_ratio * 0.3) * 100.0

    years = float(candidate_years) if candidate_years is not None else 0.0
    exp_score = min(100.0, (years / min_exp) * 100.0) if min_exp > 0 else 100.0

    # Lexical BM25 score
    try:
        ranker = BM25Ranker()
        scores = ranker.score_candidates(job_description, [candidate_text])
        raw_val = scores[0] if scores else 0.0
        semantic_score = min(100.0, max(20.0, raw_val * 4.5))
    except Exception:
        semantic_score = 50.0

    total_score = round(w_sem * semantic_score + w_key * keyword_score + w_exp * exp_score, 1)
    total_score = max(25.0, min(100.0, total_score))

    missing_desc = f", thiếu {len(missing_must)} kỹ năng bắt buộc" if missing_must else ", đạt đủ kỹ năng bắt buộc"
    rationale = (
        f"Điểm AI: {total_score}% (Từ khóa: {round(keyword_score, 1)}% | "
        f"Ngữ nghĩa: {round(semantic_score, 1)}% | Kinh nghiệm: {round(exp_score, 1)}%){missing_desc}."
    )

    return {
        "ai_score": total_score,
        "semantic_score": round(semantic_score, 1),
        "keyword_score": round(keyword_score, 1),
        "experience_score": round(exp_score, 1),
        "matched_skills": matched_must + matched_nice,
        "missing_skills": missing_must,
        "ai_rationale": rationale,
    }


def re_score_job_applications(job_id: str) -> List[Dict[str, Any]]:
    job = get_job(job_id)
    if not job:
        return []
    criteria = job.get("ai_criteria", {})
    apps = list_applications(job_id)
    scores_map = {}
    for a in apps:
        match_info = calculate_candidate_match(
            job_description=job["description"],
            ai_criteria=criteria,
            candidate_text=a.get("resume_raw_text", ""),
            candidate_skills=a.get("skills", []),
            candidate_years=a.get("years_of_experience"),
        )
        scores_map[a["id"]] = match_info
    bulk_update_ai_scores(scores_map)
    return list_applications(job_id)



# ==============================================================================
# Scorecards CRUD
# ==============================================================================

def create_scorecard(
    application_id: str,
    evaluator_name: str,
    overall_recommendation: str,
    technical_score: int = 3,
    communication_score: int = 3,
    experience_score: int = 3,
    notes: str = "",
) -> Dict[str, Any]:
    scorecard_id = f"sc_{uuid.uuid4().hex[:10]}"
    created_at = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scorecards (
                id, application_id, evaluator_name, overall_recommendation,
                technical_score, communication_score, experience_score, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scorecard_id,
                application_id,
                evaluator_name,
                overall_recommendation,
                technical_score,
                communication_score,
                experience_score,
                notes,
                created_at,
            ),
        )
        # Recalculate average rating on application
        avg_score = (technical_score + communication_score + experience_score) / 3.0
        conn.execute(
            "UPDATE applications SET overall_rating = ? WHERE id = ?",
            (round(avg_score, 1), application_id),
        )
        conn.commit()

    return {
        "id": scorecard_id,
        "application_id": application_id,
        "evaluator_name": evaluator_name,
        "overall_recommendation": overall_recommendation,
        "technical_score": technical_score,
        "communication_score": communication_score,
        "experience_score": experience_score,
        "notes": notes,
        "created_at": created_at,
    }


def list_scorecards(application_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scorecards WHERE application_id = ? ORDER BY created_at DESC",
            (application_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ==============================================================================
# Recruiter Notes CRUD
# ==============================================================================

def create_note(application_id: str, author_name: str, content: str) -> Dict[str, Any]:
    note_id = f"note_{uuid.uuid4().hex[:10]}"
    created_at = _now()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO recruiter_notes (id, application_id, author_name, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (note_id, application_id, author_name, content, created_at),
        )
        conn.commit()
    return {
        "id": note_id,
        "application_id": application_id,
        "author_name": author_name,
        "content": content,
        "created_at": created_at,
    }


def list_notes(application_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM recruiter_notes WHERE application_id = ? ORDER BY created_at ASC",
            (application_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ==============================================================================
# Interviews Scheduling CRUD
# ==============================================================================

def create_interview(
    application_id: str,
    round_type: str,
    scheduled_at: str,
    interviewer_name: str,
    duration_minutes: int = 45,
    meeting_link: str = "",
    location: str = "Online",
    notes: str = "",
) -> Dict[str, Any]:
    interview_id = f"intv_{uuid.uuid4().hex[:10]}"
    created_at = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO interviews (
                id, application_id, round_type, scheduled_at, duration_minutes,
                interviewer_name, meeting_link, location, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interview_id,
                application_id,
                round_type,
                scheduled_at,
                duration_minutes,
                interviewer_name,
                meeting_link,
                location,
                "scheduled",
                notes,
                created_at,
            ),
        )
        # Automatically advance stage to 'interviewing' if it's earlier
        app = conn.execute("SELECT stage FROM applications WHERE id = ?", (application_id,)).fetchone()
        if app and app["stage"] in ("new", "screening", "shortlisted"):
            conn.execute("UPDATE applications SET stage = 'interviewing' WHERE id = ?", (application_id,))
        conn.commit()

    return {
        "id": interview_id,
        "application_id": application_id,
        "round_type": round_type,
        "scheduled_at": scheduled_at,
        "duration_minutes": duration_minutes,
        "interviewer_name": interviewer_name,
        "meeting_link": meeting_link,
        "location": location,
        "status": "scheduled",
        "notes": notes,
        "created_at": created_at,
    }


def list_interviews(job_id: Optional[str] = None, application_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = """
        SELECT i.*, a.candidate_name, a.job_id, j.title AS job_title
        FROM interviews i
        JOIN applications a ON a.id = i.application_id
        JOIN jobs j ON j.id = a.job_id
        WHERE 1=1
    """
    params = []
    if application_id:
        query += " AND i.application_id = ?"
        params.append(application_id)
    if job_id:
        query += " AND a.job_id = ?"
        params.append(job_id)

    query += " ORDER BY i.scheduled_at ASC"

    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def update_interview_status(interview_id: str, status: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        conn.execute("UPDATE interviews SET status = ? WHERE id = ?", (status, interview_id))
        conn.commit()
        row = conn.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,)).fetchone()
    return dict(row) if row else None


# ==============================================================================
# Email Logs CRUD & Templates
# ==============================================================================

EMAIL_TEMPLATES = {
    "application_received": {
        "subject": "Xác nhận đã nhận hồ sơ ứng tuyển vị trí {{job_title}}",
        "body": "Xin chào {{candidate_name}},\n\nCảm ơn bạn đã quan tâm và nộp hồ sơ ứng tuyển vị trí {{job_title}} tại công ty. Đội ngũ tuyển dụng đã nhận được CV của bạn và sẽ tiến hành đánh giá khách quan.\n\nTrân trọng,\nĐội ngũ Tuyển dụng",
    },
    "interview_invite": {
        "subject": "Thư mời tham gia phỏng vấn vị trí {{job_title}}",
        "body": "Xin chào {{candidate_name}},\n\nChúc mừng bạn đã vượt qua vòng sàng lọc hồ sơ cho vị trí {{job_title}}! Chúng tôi trân trọng mời bạn tham gia buổi phỏng vấn {{round_type}}.\n\n- Thời gian: {{scheduled_at}}\n- Hình thức: {{meeting_link}}\n- Người phỏng vấn: {{interviewer_name}}\n\nVui lòng phản hồi để xác nhận lịch hẹn.\n\nTrân trọng,\nĐội ngũ Tuyển dụng",
    },
    "job_offer": {
        "subject": "Thư mời nhận việc (Job Offer) - Vị trí {{job_title}}",
        "body": "Xin chào {{candidate_name}},\n\nSau các vòng phỏng vấn ấn tượng, chúng tôi rất vui mừng gửi tới bạn Thư mời nhận việc chính thức cho vị trí {{job_title}}.\n\nChi tiết về chế độ đãi ngộ và lộ trình công việc được đính kèm. Chúng tôi rất mong được chào đón bạn vào đội ngũ!\n\nTrân trọng,\nPhòng Nhân sự",
    },
    "rejection": {
        "subject": "Thông báo kết quả ứng tuyển vị trí {{job_title}}",
        "body": "Xin chào {{candidate_name}},\n\nCảm ơn bạn đã dành thời gian và sự quan tâm tới cơ hội làm việc tại công ty ở vị trí {{job_title}}.\n\nSau khi cân nhắc kỹ lưỡng, chúng tôi rất tiếc phải thông báo hiện tại hồ sơ của bạn chưa phù hợp nhất với tiêu chí của đợt tuyển dụng này. Chúng tôi sẽ lưu hồ sơ của bạn vào Kho Tài năng (Talent Pool) cho các cơ hội tiếp theo.\n\nChúc bạn luôn thành công trên con đường sự nghiệp!\n\nTrân trọng,\nĐội ngũ Tuyển dụng",
    },
}


def create_email_log(
    application_id: str,
    recipient_email: str,
    template_type: str,
    subject: str,
    body: str,
) -> Dict[str, Any]:
    log_id = f"eml_{uuid.uuid4().hex[:10]}"
    sent_at = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO email_logs (id, application_id, recipient_email, template_type, subject, body, sent_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, application_id, recipient_email, template_type, subject, body, sent_at, "sent"),
        )
        conn.commit()
    return {
        "id": log_id,
        "application_id": application_id,
        "recipient_email": recipient_email,
        "template_type": template_type,
        "subject": subject,
        "body": body,
        "sent_at": sent_at,
        "status": "sent",
    }


def list_email_logs(application_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM email_logs WHERE application_id = ? ORDER BY sent_at DESC",
            (application_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ==============================================================================
# ATS Funnel Analytics & Adverse Impact (4/5ths Rule)
# ==============================================================================

def get_job_funnel_analytics(job_id: str) -> Dict[str, Any]:
    apps = list_applications(job_id)
    stages = ["new", "screening", "shortlisted", "interviewing", "offered", "hired", "rejected"]
    stage_counts = {s: 0 for s in stages}
    group_counts = {}

    for a in apps:
        stage = a.get("stage", "new")
        if stage in stage_counts:
            stage_counts[stage] += 1
        group = a.get("declared_group") or "Unknown"
        if group not in group_counts:
            group_counts[group] = {"total": 0, "shortlisted_or_above": 0}
        group_counts[group]["total"] += 1
        if stage in ("shortlisted", "interviewing", "offered", "hired"):
            group_counts[group]["shortlisted_or_above"] += 1

    # Adverse Impact (4/5ths Rule) Calculation across groups
    adverse_impact = []
    if group_counts:
        max_rate = 0.0
        for g, data in group_counts.items():
            rate = data["shortlisted_or_above"] / data["total"] if data["total"] > 0 else 0.0
            data["rate"] = rate
            if rate > max_rate:
                max_rate = rate

        for g, data in group_counts.items():
            ratio = (data["rate"] / max_rate) if max_rate > 0 else 1.0
            adverse_impact.append({
                "group": g,
                "total": data["total"],
                "passed": data["shortlisted_or_above"],
                "selection_rate": round(data["rate"], 4),
                "adverse_impact_ratio": round(ratio, 4),
                "is_adverse": ratio < 0.8,  # Below 80% marks potential adverse impact
            })

    total_apps = len(apps)
    return {
        "job_id": job_id,
        "total_applications": total_apps,
        "stage_counts": stage_counts,
        "adverse_impact": adverse_impact,
    }


# ==============================================================================
# Central Talent Pool Search
# ==============================================================================

def search_talent_pool(
    query: Optional[str] = None,
    skill: Optional[str] = None,
    min_exp: Optional[float] = None,
    stage: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sql = """
        SELECT a.*, j.title AS job_title, j.department AS job_department
        FROM applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE 1=1
    """
    params = []
    if query:
        sql += " AND (a.candidate_name LIKE ? OR a.current_title LIKE ? OR a.email LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    if skill:
        sql += " AND a.skills_json LIKE ?"
        params.append(f"%{skill}%")
    if min_exp is not None:
        sql += " AND a.years_of_experience >= ?"
        params.append(min_exp)
    if stage:
        sql += " AND a.stage = ?"
        params.append(stage)

    sql += " ORDER BY a.submitted_at DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()

    return [_format_app_item(dict(r)) for r in rows]
