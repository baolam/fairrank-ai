"""SQLite-backed persistence for job postings, candidate applications, and enterprise ATS records."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "fairrank.db"


def _migrate_table_columns(conn: sqlite3.Connection, table_name: str, expected_columns: dict) -> None:
    """Safely adds missing columns to an existing table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    for col_name, col_type in expected_columns.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")


def _create_tables(conn: sqlite3.Connection) -> None:
    # 1. Jobs Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            department TEXT DEFAULT 'Engineering',
            location TEXT DEFAULT 'Hybrid / Hanoi',
            employment_type TEXT DEFAULT 'Full-time',
            experience_level TEXT DEFAULT 'Mid-Level',
            salary_min REAL DEFAULT 0,
            salary_max REAL DEFAULT 0,
            salary_currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'published',
            deadline TEXT,
            requirements_json TEXT DEFAULT '[]'
        )
        """
    )
    _migrate_table_columns(
        conn,
        "jobs",
        {
            "department": "TEXT DEFAULT 'Engineering'",
            "location": "TEXT DEFAULT 'Hybrid / Hanoi'",
            "employment_type": "TEXT DEFAULT 'Full-time'",
            "experience_level": "TEXT DEFAULT 'Mid-Level'",
            "salary_min": "REAL DEFAULT 0",
            "salary_max": "REAL DEFAULT 0",
            "salary_currency": "TEXT DEFAULT 'USD'",
            "status": "TEXT DEFAULT 'published'",
            "deadline": "TEXT",
            "requirements_json": "TEXT DEFAULT '[]'",
            "ai_criteria_json": "TEXT DEFAULT '{}'",
        },
    )

    # 2. Applications Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES jobs (id),
            candidate_name TEXT NOT NULL,
            declared_group TEXT,
            resume_raw_text TEXT NOT NULL,
            resume_redacted_text TEXT NOT NULL,
            skills_json TEXT NOT NULL,
            years_of_experience REAL,
            submitted_at TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            current_title TEXT DEFAULT '',
            location TEXT DEFAULT '',
            linkedin_url TEXT DEFAULT '',
            stage TEXT DEFAULT 'new',
            rejection_reason TEXT DEFAULT '',
            overall_rating REAL DEFAULT 0,
            ai_score REAL DEFAULT 0.0,
            ai_rationale TEXT DEFAULT ''
        )
        """
    )
    _migrate_table_columns(
        conn,
        "applications",
        {
            "email": "TEXT DEFAULT ''",
            "phone": "TEXT DEFAULT ''",
            "current_title": "TEXT DEFAULT ''",
            "location": "TEXT DEFAULT ''",
            "linkedin_url": "TEXT DEFAULT ''",
            "stage": "TEXT DEFAULT 'new'",
            "rejection_reason": "TEXT DEFAULT ''",
            "overall_rating": "REAL DEFAULT 0",
            "ai_score": "REAL DEFAULT 0.0",
            "ai_rationale": "TEXT DEFAULT ''",
            "matched_skills_json": "TEXT DEFAULT '[]'",
            "missing_skills_json": "TEXT DEFAULT '[]'",
        },
    )

    # 3. Candidate Scorecards Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scorecards (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL REFERENCES applications (id),
            evaluator_name TEXT NOT NULL,
            overall_recommendation TEXT NOT NULL,
            technical_score INTEGER DEFAULT 3,
            communication_score INTEGER DEFAULT 3,
            experience_score INTEGER DEFAULT 3,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    # 4. Recruiter Notes Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recruiter_notes (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL REFERENCES applications (id),
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # 5. Interviews Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL REFERENCES applications (id),
            round_type TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 45,
            interviewer_name TEXT NOT NULL,
            meeting_link TEXT DEFAULT '',
            location TEXT DEFAULT 'Online',
            status TEXT DEFAULT 'scheduled',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    # 6. Email Logs Table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL REFERENCES applications (id),
            recipient_email TEXT NOT NULL,
            template_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT DEFAULT 'sent'
        )
        """
    )

    # Indexes on the FK-like lookup columns actually queried elsewhere.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications (job_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scorecards_application_id ON scorecards (application_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_recruiter_notes_application_id ON recruiter_notes (application_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interviews_application_id ON interviews (application_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_application_id ON email_logs (application_id)")

    conn.commit()


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        _create_tables(conn)
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Explicit startup hook; schema creation itself is handled lazily in get_connection()."""
    with get_connection():
        pass
