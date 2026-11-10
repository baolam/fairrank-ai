"""Experiment 07: LLM-Assisted Candidate Scoring and Bias Audit.

Demonstrates:
1. LLM API resume scoring against Job Description
2. LLM counterfactual sensitivity audit
"""

from src.contracts.llm import LLMScoringRequest, LLMBiasAuditRequest
from src.llm.scorer import score_resume_with_llm
from src.llm.auditor import audit_resume_with_llm


def main():
    print("=" * 60)
    print("EXPERIMENT 07: LLM-ASSISTED SCORING & BIAS AUDIT")
    print("=" * 60)

    job_description = """
    Lead Data Scientist
    Requirements:
    - 5+ years experience building predictive models and NLP applications.
    - Strong skills in PyTorch, Python, SQL, and Docker.
    - Track record of deploying machine learning systems to production.
    """

    resume_text = """
    Candidate: Lakisha Washington
    Location: Atlanta, GA

    Summary:
    Data Scientist with 5 years of industry experience developing end-to-end NLP and tabular ML pipelines.
    Expert in PyTorch, transformers, scikit-learn, and SQL. Deployed 4 production services using Docker and FastAPI.
    """

    print("1. Querying LLM Candidate Scorer...")
    scoring_req = LLMScoringRequest(
        job_title="Lead Data Scientist",
        job_description=job_description,
        resume_text=resume_text,
        candidate_id="cand_nlp_01",
        provider="gemini",
    )
    score_res = score_resume_with_llm(scoring_req)

    print(f"  Relevance Grade       : {score_res.relevance_grade.name} ({int(score_res.relevance_grade)})")
    print(f"  Fit Score             : {score_res.fit_score:.2f}")
    print(f"  Key Qualifications    : {score_res.key_qualifications}")
    print(f"  Missing Qualifications: {score_res.missing_qualifications}")
    print(f"  Rationale             : {score_res.rationale}")
    print(f"  Latency               : {score_res.latency_ms:.1f} ms")

    print("\n2. Querying LLM Demographic Proxy & Bias Auditor...")
    variants = [
        {"name": "Lakisha Washington", "group": "Black_female"},
        {"name": "Jamal Washington", "group": "Black_male"},
        {"name": "Emily Miller", "group": "White_female"},
        {"name": "Brad Miller", "group": "White_male"},
    ]
    audit_req = LLMBiasAuditRequest(
        job_description=job_description,
        original_text=resume_text,
        counterfactual_variants=variants,
        provider="gemini",
    )
    audit_res = audit_resume_with_llm(audit_req)

    print(f"  Demographically Sensitive: {audit_res.is_demographically_sensitive}")
    print(f"  Perceived Bias Score     : {audit_res.perceived_bias_score:.3f}")
    print(f"  Audit Findings           : {audit_res.audit_findings}")
    print(f"  Proxy Tokens Detected    : {audit_res.proxy_tokens_detected}")
    print(f"  Recommendation           : {audit_res.recommendation}")

    print("\nLLM API scoring & audit pipeline completed successfully.")


if __name__ == "__main__":
    main()
