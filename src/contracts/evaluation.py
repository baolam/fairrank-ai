"""Data contracts for evaluation metrics, disparity audits, and statistical hypotheses (Stage 6).

Enforces mathematical consistency for nDCG@10, exposure gaps, noise floor,
and H1-H5 validation.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from src.contracts.stimuli import IntersectionalGroup


class QueryUtilityMetrics(BaseModel):
    """Utility metrics computed for a single query pool."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str
    pool_size: int
    ndcg_at_10: float = Field(..., ge=0.0, le=1.0, description="Normalized Discounted Cumulative Gain at min(10, N_q)")
    mrr: float = Field(..., ge=0.0, le=1.0, description="Mean Reciprocal Rank for first Good Fit (0 if none)")
    recall_at_10: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recall@10 for Good Fit candidates")
    ideal_dcg: float = Field(..., ge=0.0, description="IDCG denominator")
    has_good_fit: bool


class DemographicExposureSummary(BaseModel):
    """Exposure statistics aggregated per demographic group."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    group: IntersectionalGroup
    candidate_count: int = Field(..., ge=0)
    selection_rate_at_10: float = Field(..., ge=0.0, le=1.0, description="Proportion with rank <= 10")
    mean_exposure_at_10: float = Field(..., ge=0.0, le=1.0, description="Mean exposure over members")


class DisparityAuditResult(BaseModel):
    """Audit of demographic disparity for a specific query or dataset aggregate."""
    model_config = ConfigDict(extra="forbid")

    black_white_signed_exposure_gap: float = Field(..., description="Black exposure minus White exposure")
    black_white_abs_exposure_gap: float = Field(..., ge=0.0, description="Absolute Black-White exposure gap")
    female_male_signed_exposure_gap: float = Field(..., description="Female exposure minus Male exposure")
    female_male_abs_exposure_gap: float = Field(..., ge=0.0, description="Absolute Female-Male exposure gap")
    within_group_noise_floor: float = Field(..., ge=0.0, description="Matched within-group name-swap noise floor")
    cross_group_excess: float = Field(..., description="abs_gap minus within_group_noise_floor")
    max_intersectional_gap: float = Field(..., ge=0.0, description="Max minus min among 4 intersectional groups")
    intersectional_excess: float = Field(..., description="Max intersectional gap minus larger marginal gap")
    group_summaries: Dict[IntersectionalGroup, DemographicExposureSummary]


class HypothesisTestResult(BaseModel):
    """Result of confirmatory hypothesis testing (H1-H5) with Holm adjustment."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis_id: str = Field(..., description="e.g. H1, H2, H3, H4, H5")
    description: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    threshold: float
    p_value_raw: float
    p_value_holm_adjusted: float
    is_supported: bool
    notes: Optional[str] = None


class Stage6AuditReport(BaseModel):
    """Comprehensive Stage 6 audit report integrating all evaluation metrics."""
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    model_name: str
    intervention: str
    condition: str
    mean_ndcg_at_10: float
    relative_utility_loss_pct: Optional[float] = None
    disparity: DisparityAuditResult
    hypotheses: List[HypothesisTestResult]
