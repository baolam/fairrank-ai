"""Text normalization module adhering to Stage 1 constraints.

Rules from proposal:
- Unicode normalization (NFKC).
- Whitespace stripping and uniform space collapsing.
- Markup cleaning while strictly preserving section boundaries and qualification content.
"""

import re
import unicodedata
import hashlib


def normalize_text(text: str) -> str:
    """Normalizes text with deterministic Unicode and whitespace handling."""
    if not text:
        return ""

    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Strip HTML/XML corrupted markup tags if any, preserving content
    normalized = re.sub(r"<[^>]+>", " ", normalized)

    # 3. Standardize linebreaks while preserving section paragraphs
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Collapse runs of horizontal whitespace (spaces, tabs) into single space
    lines = []
    for line in normalized.split("\n"):
        clean_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(clean_line)

    # 5. Collapse excessive empty lines to max 2 newlines (paragraph boundary)
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return result.strip()


def compute_content_hash(text: str) -> str:
    """Computes a deterministic SHA-256 hash for exact deduplication."""
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()
