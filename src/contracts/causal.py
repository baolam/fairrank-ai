"""Data contracts for PopResume causal graph and Path-Specific Effect (PSE) estimation (Stage 5).

Defines structures for protected attribute A, confounders Z, qualification mediators B,
proxy mediators R, and standardized PSE estimates.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class PopResumeProfile(BaseModel):
    """Synthetic resume profile from sumin-yu/PopResume text configuration."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str
    occupation: str
    race: str
    sex: str
    education_level: str
    years_experience: float
    state_location: str
    injected_name: str
    intact_text: str
    name_redacted_text: str
    name_location_redacted_text: str


class CausalVariableSet(BaseModel):
    """Specification of variables in causal graph DAG."""
    protected_attribute: str = Field("A", description="Protected attribute: Race or Sex")
    confounders: List[str] = Field(default_factory=lambda: ["Z_age", "Z_socioeconomic"])
    qualification_mediators: List[str] = Field(default_factory=lambda: ["B_education", "B_experience"])
    proxy_mediators: List[str] = Field(default_factory=lambda: ["R_name", "R_location"])


class PSEEstimate(BaseModel):
    """Standardized Path-Specific Effect estimate."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    occupation: str
    contrast: str = Field(..., description="e.g. 'Black vs White' or 'Female vs Male'")
    pathway: str = Field(..., description="'proxy' or 'qualification'")
    condition: str = Field(..., description="'intact', 'name_redacted', 'name_loc_redacted'")
    standardized_pse: float = Field(..., description="PSE standardized by intact-text within-occupation score std")
    ci_lower: float
    ci_upper: float
    std_error: float


class OccupationCausalReport(BaseModel):
    """Causal estimation report for an occupation slice."""
    model_config = ConfigDict(extra="forbid")

    occupation: str
    sample_size: int
    score_standard_deviation_intact: float
    estimates: List[PSEEstimate]
    proxy_reduction_pct: Optional[float] = None
    qualification_change_abs: Optional[float] = None
