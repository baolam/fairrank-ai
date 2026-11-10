"""TMG301 Data Contracts Package.

Exposes strictly validated data contracts across all pipeline stages:
- raw_data: Stage 1 Raw and normalized datasets
- stimuli: Stage 2 Demographic names, templates, variants
- ranking: Stage 3 Scored & ranked candidates, pools, exposure
- mitigation: Stage 4 Redaction, CDA, Greedy Reranker
- causal: Stage 5 PopResume causal graph & PSE estimates
- evaluation: Stage 6 Metrics, disparities, hypotheses H1-H5
- llm: LLM API integration requests and responses
"""

from src.contracts.raw_data import (
    RelevanceLabel,
    SplitType,
    RawJobDescription,
    RawResume,
    LabeledPair,
    JobPool,
)
from src.contracts.stimuli import (
    PerceivedRace,
    PerceivedGender,
    IntersectionalGroup,
    StimulusPartition,
    DemographicName,
    TemplateType,
    CandidateVariant,
)
from src.contracts.ranking import (
    ScoredCandidate,
    RankedCandidate,
    RankedPool,
)
from src.contracts.mitigation import (
    CDATrainingVariant,
    CDAMinibatchItem,
    RerankerCandidateInput,
    RerankerPoolInput,
    RerankerCandidateOutput,
)
from src.contracts.evaluation import (
    QueryUtilityMetrics,
    DemographicExposureSummary,
    DisparityAuditResult,
    HypothesisTestResult,
    Stage6AuditReport,
)
from src.contracts.causal import (
    PopResumeProfile,
    CausalVariableSet,
    PSEEstimate,
    OccupationCausalReport,
)
from src.contracts.llm import (
    LLMProviderType,
    LLMScoringRequest,
    LLMScoringResponse,
    LLMBiasAuditRequest,
    LLMBiasAuditResponse,
)

__all__ = [
    "RelevanceLabel",
    "SplitType",
    "RawJobDescription",
    "RawResume",
    "LabeledPair",
    "JobPool",
    "PerceivedRace",
    "PerceivedGender",
    "IntersectionalGroup",
    "StimulusPartition",
    "DemographicName",
    "TemplateType",
    "CandidateVariant",
    "ScoredCandidate",
    "RankedCandidate",
    "RankedPool",
    "CDATrainingVariant",
    "CDAMinibatchItem",
    "RerankerCandidateInput",
    "RerankerPoolInput",
    "RerankerCandidateOutput",
    "QueryUtilityMetrics",
    "DemographicExposureSummary",
    "DisparityAuditResult",
    "HypothesisTestResult",
    "Stage6AuditReport",
    "PopResumeProfile",
    "CausalVariableSet",
    "PSEEstimate",
    "OccupationCausalReport",
    "LLMProviderType",
    "LLMScoringRequest",
    "LLMScoringResponse",
    "LLMBiasAuditRequest",
    "LLMBiasAuditResponse",
]
