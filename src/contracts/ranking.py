"""Data contracts for scoring and ranking outputs (Stage 3).

Ensures deterministic ranking representations, stable tie-breaking,
and explicit exposure definitions.
"""

import math
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel


class ScoredCandidate(BaseModel):
    """A single candidate variant evaluated by a retrieval model against a job query."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str = Field(..., description="Variant identifier")
    base_resume_id: str = Field(..., description="Base resume ID")
    job_id: str = Field(..., description="Target job query ID")
    group: Optional[IntersectionalGroup] = Field(None, description="Demographic group")
    relevance_grade: RelevanceLabel = Field(..., description="Ground truth relevance label {0, 1, 2}")
    raw_score: float = Field(..., description="Raw model score (cosine similarity or BM25)")
    normalized_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Min-max normalized score in [0, 1]")
    tie_breaker_id: str = Field(..., description="Deterministic unique string for stable tie-breaking")


class RankedCandidate(BaseModel):
    """A scored candidate assigned a concrete 1-based rank position in a pool."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str = Field(..., description="Variant identifier")
    base_resume_id: str = Field(..., description="Base resume ID")
    group: Optional[IntersectionalGroup] = Field(None, description="Demographic group")
    relevance_grade: RelevanceLabel = Field(..., description="Ground truth relevance label")
    raw_score: float = Field(..., description="Raw model score")
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score a_qi")
    rank: int = Field(..., ge=1, description="1-based integer rank (1 is top)")
    exposure_at_10: float = Field(..., ge=0.0, le=1.0, description="Exposure e(10) = 1/log2(rank+1) if rank<=10 else 0")

    @classmethod
    def calculate_exposure(cls, rank: int, cutoff_k: int = 10) -> float:
        """Computes exposure discount e(k) = 1(rank <= k) / log2(rank + 1)."""
        if rank <= 0:
            raise ValueError(f"Rank must be >= 1, got {rank}")
        if rank <= cutoff_k:
            return 1.0 / math.log2(rank + 1)
        return 0.0


class RankedPool(BaseModel):
    """Complete ranked candidates pool for query q under a specific experimental condition."""
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="Job identifier")
    model_name: str = Field(..., description="Identifier of scoring model (e.g. bm25, sbert, cda)")
    intervention: str = Field(..., description="Intervention condition (none, redaction, reranking, cda)")
    composition: str = Field(..., description="Pool composition (balanced, 70_30_black, 70_30_white)")
    cutoff_k: int = Field(default=10, ge=1, description="Top-k evaluation cutoff")
    ranked_candidates: List[RankedCandidate] = Field(..., description="Ordered list of ranked candidates")
    total_candidates: int = Field(..., ge=1, description="Total candidates count N_q")

    @field_validator("ranked_candidates")
    @classmethod
    def validate_ranks_strictly_ordered(cls, v):
        for idx, item in enumerate(v):
            expected_rank = idx + 1
            if item.rank != expected_rank:
                raise ValueError(f"Candidate rank mismatch at index {idx}: expected {expected_rank}, got {item.rank}")
        return v
