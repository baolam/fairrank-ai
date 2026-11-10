"""Router for document parsing and candidate ingestion."""

from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from src.parser.document_loader import (
    load_text_from_bytes,
    validate_resume_file,
    ensure_extractable_text,
)
from src.parser.resume_extractor import extract_resume_entities, ParsedResume

router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion & Parsing"])


@router.post("/parse-file", response_model=ParsedResume)
async def parse_single_file(file: UploadFile = File(...)):
    """Uploads and parses a single PDF, DOCX, or TXT resume."""
    try:
        content = await file.read()
        validate_resume_file(file.filename or "resume", content)
        text = load_text_from_bytes(content, file.filename or "resume.txt")
        ensure_extractable_text(text)
        parsed = extract_resume_entities(text, filename_hint=file.filename)
        return parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")


@router.post("/parse-files", response_model=List[ParsedResume])
async def parse_multiple_files(files: List[UploadFile] = File(...)):
    """Uploads and batch-parses multiple resumes."""
    results = []
    for file in files:
        try:
            content = await file.read()
            validate_resume_file(file.filename or "resume", content)
            text = load_text_from_bytes(content, file.filename or "resume.txt")
            ensure_extractable_text(text)
            parsed = extract_resume_entities(text, filename_hint=file.filename)
            results.append(parsed)
        except Exception:
            # Continue parsing others if one fails
            continue
    return results


@router.post("/parse-text", response_model=ParsedResume)
async def parse_raw_text(text: str = Form(...), candidate_name: str = Form(None)):
    """Parses raw plain text resume with optional candidate name hint."""
    parsed = extract_resume_entities(text, filename_hint=candidate_name)
    return parsed
