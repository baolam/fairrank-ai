"""Document loader for extracting plain text from PDF, DOCX, and TXT files."""

import io
from pathlib import Path
from typing import Union
from pypdf import PdfReader
import docx
from src.data_prep.normalizer import normalize_text

ALLOWED_RESUME_SUFFIXES = {".pdf", ".docx", ".doc", ".txt", ".md"}
MAX_RESUME_FILE_BYTES = 10 * 1024 * 1024  # 10MB
MIN_EXTRACTED_TEXT_CHARS = 30


class UnsupportedDocumentError(ValueError):
    """Raised when an uploaded resume file fails format/size/content validation."""


def validate_resume_file(filename: str, content: bytes) -> None:
    """Rejects disallowed file types, oversized uploads, and empty files up front."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_RESUME_SUFFIXES:
        raise UnsupportedDocumentError(
            f"Định dạng file không được hỗ trợ: {suffix or 'không rõ'}. "
            "Chỉ chấp nhận PDF, DOCX, hoặc TXT."
        )
    if len(content) == 0:
        raise UnsupportedDocumentError("File rỗng, vui lòng chọn lại.")
    if len(content) > MAX_RESUME_FILE_BYTES:
        size_mb = len(content) / 1_048_576
        raise UnsupportedDocumentError(f"File quá lớn ({size_mb:.1f}MB). Giới hạn tối đa 10MB.")


def ensure_extractable_text(raw_text: str) -> None:
    """Catches the common silent failure: a scanned/image-only PDF with no text layer."""
    if len(raw_text.strip()) < MIN_EXTRACTED_TEXT_CHARS:
        raise UnsupportedDocumentError(
            "Không trích xuất được nội dung văn bản từ file (có thể là bản scan hình ảnh). "
            "Vui lòng dùng PDF có lớp văn bản chọn được, hoặc nộp bằng .docx/.txt."
        )


def extract_text_from_pdf_stream(stream: io.BytesIO) -> str:
    """Extracts text from a PDF stream using pypdf."""
    reader = PdfReader(stream)
    pages_text = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            pages_text.append(extracted)
    return "\n\n".join(pages_text)


def extract_text_from_docx_stream(stream: io.BytesIO) -> str:
    """Extracts text from a DOCX stream using python-docx."""
    doc = docx.Document(stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def load_text_from_bytes(content: bytes, filename: str) -> str:
    """Loads and normalizes text from in-memory bytes based on filename extension."""
    suffix = Path(filename).suffix.lower()
    raw_text = ""
    stream = io.BytesIO(content)

    if suffix == ".pdf":
        raw_text = extract_text_from_pdf_stream(stream)
    elif suffix in (".docx", ".doc"):
        raw_text = extract_text_from_docx_stream(stream)
    elif suffix in (".txt", ".md", ".json"):
        raw_text = content.decode("utf-8", errors="replace")
    else:
        # Fallback to UTF-8 decoding
        raw_text = content.decode("utf-8", errors="replace")

    return normalize_text(raw_text)


def load_text_from_file(file_path: Union[str, Path]) -> str:
    """Loads and normalizes text from a local disk file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        content = f.read()

    return load_text_from_bytes(content, path.name)
