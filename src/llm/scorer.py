"""High-level LLM Candidate Scoring module conforming to data contracts."""

from src.contracts.llm import LLMScoringRequest, LLMScoringResponse
from src.contracts.raw_data import RelevanceLabel
from src.llm.client import UnifiedLLMClient
from src.llm.prompts import SYSTEM_SCORING_PROMPT, build_scoring_user_prompt


def score_resume_with_llm(request: LLMScoringRequest) -> LLMScoringResponse:
    """Invokes LLM API to score a resume against a job description, returning a validated response."""
    client = UnifiedLLMClient(provider=request.provider)
    prompt = build_scoring_user_prompt(request.job_description, request.resume_text)

    raw_response = client.generate_json_response(SYSTEM_SCORING_PROMPT, prompt)

    return LLMScoringResponse(
        candidate_id=request.candidate_id,
        relevance_grade=RelevanceLabel(int(raw_response.get("relevance_grade", 1))),
        fit_score=float(raw_response.get("fit_score", 0.5)),
        key_qualifications=raw_response.get("key_qualifications", []),
        missing_qualifications=raw_response.get("missing_qualifications", []),
        rationale=raw_response.get("rationale", "Evaluated by LLM."),
        token_usage=raw_response.get("token_usage", {}),
        latency_ms=raw_response.get("latency_ms", 0.0),
    )
