"""Data contracts for fairness mitigations (Stage 4).

Defines structures for Redaction, Counterfactual Data Augmentation (CDA),
and Greedy Exposure-Aware Reranking.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from src.contracts.stimuli import IntersectionalGroup


class CDATrainingVariant(BaseModel):
    """A training variant pair for CDA fine-tuning."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    base_resume_id: str
    group: IntersectionalGroup
    rendered_text: str


class CDAMinibatchItem(BaseModel):
    """Query-resume item within a CDA minibatch."""
    model_config = ConfigDict(extra="forbid")

    job_id: str
    job_text: str
    base_resume_id: str
    relevance_grade: int
    variants: List[CDATrainingVariant] = Field(..., min_length=2, description="Cross-group name variants")


class RerankerCandidateInput(BaseModel):
    """Input representation of a candidate for exposure-aware greedy reranking."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str
    base_resume_id: str
    group: IntersectionalGroup = Field(..., description="Protected group label used for exposure target")
    frozen_score: float = Field(..., description="Raw frozen model score")
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Min-max normalized score a_qi in [0, 1]")
    relevance_grade: int = Field(..., description="Ground truth label (kept for evaluation, hidden from reranker)")
    tie_breaker_id: str


class RerankerPoolInput(BaseModel):
    """Pool input for the greedy reranker."""
    model_config = ConfigDict(extra="forbid")

    job_id: str
    candidates: List[RerankerCandidateInput] = Field(..., min_length=1)
    lambda_penalty: float = Field(..., ge=0.0, description="Fairness penalty strength lambda in {0, 0.1, 1, 10}")
    cutoff_k: int = Field(default=10, ge=1)
    group_counts: Dict[IntersectionalGroup, int] = Field(..., description="Counts n_g of each group present")


class RerankerCandidateOutput(BaseModel):
    """Candidate output produced by the reranker."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str
    base_resume_id: str
    group: IntersectionalGroup
    relevance_grade: int
    reranked_rank: int = Field(..., ge=1)
    original_rank: int = Field(..., ge=1)
    normalized_score: float
    marginal_objective_gain: float
