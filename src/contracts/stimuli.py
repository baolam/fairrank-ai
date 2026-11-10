"""Data contracts for demographic stimuli and injected candidate variants (Stage 2).

Defines names, perceived demographic categories, rendering templates,
and counterfactual variant schemas.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PerceivedRace(str, Enum):
    BLACK = "Black"
    WHITE = "White"


class PerceivedGender(str, Enum):
    FEMALE = "Female"
    MALE = "Male"


class IntersectionalGroup(str, Enum):
    BLACK_FEMALE = "Black_female"
    BLACK_MALE = "Black_male"
    WHITE_FEMALE = "White_female"
    WHITE_MALE = "White_male"


class StimulusPartition(str, Enum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class DemographicName(BaseModel):
    """Audited demographic name entry from stimulus manifest."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    name_id: str = Field(..., description="Unique deterministic identifier (e.g. name_BF_01)")
    full_name: str = Field(..., min_length=2, description="Candidate full name")
    race: PerceivedRace = Field(..., description="Perceived race category")
    gender: PerceivedGender = Field(..., description="Perceived gender category")
    group: IntersectionalGroup = Field(..., description="Intersectional perceived demographic group")
    partition: StimulusPartition = Field(..., description="Usage partition: train, val, or test")
    source: str = Field("Wilson-Caliskan / Public Census", description="Source of empirical validation")
    token_length_estimate: int = Field(default=2, ge=1, description="Estimated token length")
    frequency_band: Optional[str] = Field(None, description="Matched frequency band")


class TemplateType(str, Enum):
    """Fixed templates locked by proposal to prevent confounding."""
    TRAIN_TOP_LINE = "top_name_line"
    VAL_CONTACT_HEADER = "labeled_contact_header"
    TEST_BELOW_SUMMARY = "name_below_summary"
    REDACTED_NEUTRAL = "redacted_neutral"


class CandidateVariant(BaseModel):
    """Resume text variant with injected demographic stimulus or neutral redaction."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    variant_id: str = Field(..., description="Unique variant ID (e.g. res_001::name_BF_01)")
    base_resume_id: str = Field(..., description="Underlying base resume identifier")
    name_id: Optional[str] = Field(None, description="Injected name ID (None if redacted)")
    candidate_name: str = Field(..., description="Injected name or neutral token")
    group: Optional[IntersectionalGroup] = Field(None, description="Demographic group of injected name")
    template_type: TemplateType = Field(..., description="Rendering template used for insertion")
    rendered_text: str = Field(..., min_length=10, description="Full rendered text ready for encoding")
    is_redacted: bool = Field(default=False, description="Whether this candidate is an anonymized control")
