"""Shared helper for streaming candidate CV PDFs, used by both the jobs and candidates routers."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi.responses import FileResponse, Response

from src.storage.cv_pdf import generate_candidate_cv_pdf

BLIND_CV_FILENAME = "CV_blind_candidate.pdf"


def build_cv_pdf_response(
    app: Dict[str, Any],
    job: Optional[Dict[str, Any]],
    blind: bool,
) -> Response:
    """Streams the stored raw PDF when one exists (non-blind requests only), else renders one on the fly.

    In blind mode the filename must never reveal the candidate's identity, so it is
    always a fixed generic name rather than one derived from candidate_name.
    """
    resume_pdf_path = Path("data") / "resumes" / f"{app['id']}.pdf"
    if resume_pdf_path.exists() and not blind:
        return FileResponse(
            str(resume_pdf_path),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="CV_{app["candidate_name"]}.pdf"'},
        )

    pdf_bytes = generate_candidate_cv_pdf(app=app, job=job, blind_mode=blind)
    if blind:
        filename = BLIND_CV_FILENAME
    else:
        safe_name = re.sub(r"[^\w\s-]", "", app.get("candidate_name", "candidate")).strip().replace(" ", "_")
        filename = f"CV_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
