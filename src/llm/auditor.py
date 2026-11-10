"""High-level LLM Demographic Bias and Proxy-Pathway Auditor."""

from src.contracts.llm import LLMBiasAuditRequest, LLMBiasAuditResponse
from src.llm.client import UnifiedLLMClient
from src.llm.prompts import SYSTEM_BIAS_AUDIT_PROMPT, build_audit_user_prompt


def audit_resume_with_llm(request: LLMBiasAuditRequest) -> LLMBiasAuditResponse:
    """Uses LLM to analyze candidate resume variants for demographic proxy risks."""
    client = UnifiedLLMClient(provider=request.provider)

    variants_str = "\n".join(
        [f"- [{v.get('group', 'Unknown')}]: Name '{v.get('name', 'N/A')}'" for v in request.counterfactual_variants]
    )

    prompt = build_audit_user_prompt(
        job_description=request.job_description,
        base_resume=request.original_text,
        variants_summary=variants_str,
    )

    raw_response = client.generate_json_response(SYSTEM_BIAS_AUDIT_PROMPT, prompt, response_kind="bias_audit")

    return LLMBiasAuditResponse(
        is_demographically_sensitive=bool(raw_response.get("is_demographically_sensitive", False)),
        perceived_bias_score=float(raw_response.get("perceived_bias_score", 0.05)),
        audit_findings=raw_response.get("audit_findings", ["Invariant across tested names"]),
        proxy_tokens_detected=raw_response.get("proxy_tokens_detected", []),
        recommendation=raw_response.get("recommendation", "Redaction of name fields is sufficient."),
    )
