"""Shared dependencies and model caching for FastAPI application."""

from typing import Optional, Any
from src.models.bm25_ranker import BM25Ranker

_bm25_instance: Optional[BM25Ranker] = None
_sbert_instance: Optional[Any] = None


def get_bm25_ranker() -> BM25Ranker:
    """Returns singleton BM25Ranker instance."""
    global _bm25_instance
    if _bm25_instance is None:
        _bm25_instance = BM25Ranker()
    return _bm25_instance


def get_sbert_ranker():
    """Lazily returns singleton SBERTRanker instance."""
    global _sbert_instance
    if _sbert_instance is None:
        from src.models.sbert_ranker import SBERTRanker
        _sbert_instance = SBERTRanker()
    return _sbert_instance
