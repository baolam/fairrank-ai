"""Demo-grade recruiter access gate.

A single shared-secret code (not a real auth system) protects the
Recruiter-only endpoints so a casual visitor to the public demo cannot
browse submitted candidate applications. Set RECRUITER_ACCESS_CODE in the
environment to override the default demo code.
"""

import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["Recruiter Access"])

DEFAULT_RECRUITER_CODE = "fairrank-demo"


def _expected_code() -> str:
    return os.environ.get("RECRUITER_ACCESS_CODE", DEFAULT_RECRUITER_CODE)


def require_recruiter_access(x_recruiter_code: str = Header(default="")) -> None:
    """FastAPI dependency: raises 401 unless the caller sent the correct recruiter code via header.

    Use this for every recruiter-only endpoint. The query-param variant below is a
    narrow, deliberate exception for direct-link PDF streaming only (a plain <a>
    tag can't set a custom header) — it must not be used as the general-purpose
    auth check, since query strings leak into server access logs, browser history,
    and Referer headers.
    """
    if x_recruiter_code == _expected_code():
        return
    raise HTTPException(status_code=401, detail="Invalid or missing recruiter access code.")


def require_recruiter_access_pdf(
    x_recruiter_code: str = Header(default=""),
    code: Optional[str] = Query(default=None),
) -> None:
    """FastAPI dependency for the CV PDF endpoints only: accepts the code via header OR `?code=` query param."""
    expected = _expected_code()
    if x_recruiter_code == expected or code == expected:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing recruiter access code.")


class RecruiterLoginRequest(BaseModel):
    code: str


@router.post("/recruiter-login")
def recruiter_login(req: RecruiterLoginRequest):
    if req.code != _expected_code():
        raise HTTPException(status_code=401, detail="Incorrect recruiter access code.")
    return {"ok": True}
