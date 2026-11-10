"""SQLite-backed persistence for job postings and candidate applications.

Demo-grade storage: a single local file, no migrations. Good enough to let
a Candidate role and a Recruiter role interact asynchronously against the
same running backend.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "fairrank.db"


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
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
            submitted_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


@contextmanager
def get_connection():
    """Opens a connection, ensuring the schema exists.

    Schema creation runs on every connection (idempotent via IF NOT EXISTS)
    rather than only in init_db(), since ASGI startup events do not fire for
    a bare `TestClient(app)` outside a `with` block.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        _create_tables(conn)
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Explicit startup hook; schema creation itself is handled lazily in get_connection()."""
    with get_connection():
        pass
