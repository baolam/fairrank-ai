"""Data contracts for LLM API integration.

Defines request/response schemas for LLM-based candidate scoring,
demographic bias auditing, and explainable resume screening.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from src.contracts.raw_data import RelevanceLabel


class LLMProviderType(str):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_OLLAMA = "ollama"


class LLMScoringRequest(BaseModel):
    """Payload sent to LLM for candidate resume-job fit assessment."""
    model_config = ConfigDict(extra="forbid")

    job_title: str
    job_description: str
    resume_text: str
    candidate_id: str
    anonymize_demographics: bool = False
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    provider: str = Field(default="gemini")
    model_name: Optional[str] = None


class LLMScoringResponse(BaseModel):
    """Structured response parsed from LLM evaluation."""
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    relevance_grade: RelevanceLabel = Field(..., description="0: No Fit, 1: Potential Fit, 2: Good Fit")
    fit_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score [0.0 - 1.0]")
    key_qualifications: List[str] = Field(default_factory=list, description="Extracted relevant skills & experience")
    missing_qualifications: List[str] = Field(default_factory=list, description="Gaps identified against job requirements")
    rationale: str = Field(..., description="Detailed explanation of the rating")
    token_usage: Dict[str, int] = Field(default_factory=dict)
    latency_ms: float = Field(default=0.0)


class LLMBiasAuditRequest(BaseModel):
    """Request for LLM to audit a resume ranking pool for demographic proxy sensitivity."""
    model_config = ConfigDict(extra="forbid")

    job_description: str
    original_text: str
    counterfactual_variants: List[Dict[str, str]] = Field(
        ..., description="List of dictionaries with name, group, and rendered_text"
    )
    provider: str = Field(default="gemini")


class LLMBiasAuditResponse(BaseModel):
    """Structured response from LLM bias audit."""
    model_config = ConfigDict(extra="forbid")

    is_demographically_sensitive: bool
    perceived_bias_score: float = Field(..., ge=0.0, le=1.0, description="0=completely invariant, 1=high sensitivity")
    audit_findings: List[str] = Field(default_factory=list)
    proxy_tokens_detected: List[str] = Field(default_factory=list, description="Detected demographic proxy indicators")
    recommendation: str
