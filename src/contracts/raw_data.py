"""Data contracts for raw and normalized inputs (Stage 1).

Enforces strict schemas for Resume-Job Fit and PopResume data structures,
ensuring normalization integrity and label validity across all pipeline stages.
"""

from enum import IntEnum, Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RelevanceLabel(IntEnum):
    """Graded relevance according to proposal: No Fit (0), Potential Fit (1), Good Fit (2)."""
    NO_FIT = 0
    POTENTIAL_FIT = 1
    GOOD_FIT = 2


class SplitType(str, Enum):
    """Job-disjoint dataset partitions."""
    TRAIN = "train"
    VAL = "val"
    TEST_INDOMAIN = "test_indomain"
    TEST_HOLDOUT = "test_holdout"


class RawJobDescription(BaseModel):
    """Job description entity with occupation classification."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str = Field(..., description="Unique deterministic identifier of the job")
    raw_text: str = Field(..., min_length=10, description="Raw text of the job description")
    normalized_text: str = Field(..., min_length=10, description="Cleaned Unicode/whitespace text")
    content_hash: str = Field(..., min_length=16, description="SHA256 hash of normalized text")
    soc_code: Optional[str] = Field(None, description="Standard Occupational Classification code")
    soc_title: Optional[str] = Field(None, description="SOC occupational category title")
    split: SplitType = Field(SplitType.TRAIN, description="Assigned job-disjoint partition")


class RawResume(BaseModel):
    """Base resume entity before any demographic stimulus injection."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    resume_id: str = Field(..., description="Unique deterministic identifier of the base resume")
    raw_text: str = Field(..., min_length=10, description="Raw text of the resume")
    normalized_text: str = Field(..., min_length=10, description="Cleaned Unicode/whitespace text")
    content_hash: str = Field(..., min_length=16, description="SHA256 hash of normalized text")
    near_duplicate_cluster_id: Optional[str] = Field(None, description="Cluster ID for near duplicates")


class LabeledPair(BaseModel):
    """Judged Resume-Job pair with benchmark label."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_id: str = Field(..., description="Unique ID for pair (e.g. job_id::resume_id)")
    job_id: str = Field(..., description="Reference to RawJobDescription.job_id")
    resume_id: str = Field(..., description="Reference to RawResume.resume_id")
    relevance_grade: RelevanceLabel = Field(..., description="Relevance grade {0, 1, 2}")

    @field_validator("relevance_grade", mode="before")
    @classmethod
    def parse_relevance_label(cls, v):
        if isinstance(v, str):
            mapping = {
                "no fit": RelevanceLabel.NO_FIT,
                "0": RelevanceLabel.NO_FIT,
                "potential fit": RelevanceLabel.POTENTIAL_FIT,
                "1": RelevanceLabel.POTENTIAL_FIT,
                "good fit": RelevanceLabel.GOOD_FIT,
                "2": RelevanceLabel.GOOD_FIT,
            }
            clean_v = v.strip().lower()
            if clean_v in mapping:
                return mapping[clean_v]
        return RelevanceLabel(int(v))


class JobPool(BaseModel):
    """Judged candidate pool for a specific job query q."""
    model_config = ConfigDict(extra="forbid")

    job: RawJobDescription = Field(..., description="Job query specification")
    candidate_resumes: List[RawResume] = Field(..., description="Candidate resumes judged for this job")
    labels: List[LabeledPair] = Field(..., description="Judged labels for each candidate")
    pool_size: int = Field(..., description="Candidate count N_q in pool")

    @field_validator("pool_size")
    @classmethod
    def validate_pool_size(cls, v, info):
        resumes = info.data.get("candidate_resumes")
        if resumes is not None and len(resumes) != v:
            raise ValueError(f"pool_size {v} does not match resumes count {len(resumes)}")
        return v
