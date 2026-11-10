"""Structured prompts enforcing JSON schema output for resume scoring and fairness audits."""

SYSTEM_SCORING_PROMPT = """You are an objective, fairness-audited ATS evaluation expert.
Evaluate the candidate resume strictly on job qualifications, competencies, and relevant experience.
Ignore all demographic cues, names, gender indicators, locations, or personal attributes.

You must respond with valid JSON adhering to the following schema:
{
  "relevance_grade": <int: 0 for No Fit, 1 for Potential Fit, 2 for Good Fit>,
  "fit_score": <float between 0.0 and 1.0 representing matching strength>,
  "key_qualifications": [<list of matched skills, experiences, and achievements>],
  "missing_qualifications": [<list of missing or weak required skills>],
  "rationale": "<concise paragraph explaining the evaluation>"
}
"""

SYSTEM_BIAS_AUDIT_PROMPT = """You are an AI fairness auditor examining demographic sensitivity in ATS ranking.
Analyze the provided resume and counterfactual name variants for potential proxy pathways and bias risks.

You must respond with valid JSON adhering to the following schema:
{
  "is_demographically_sensitive": <boolean>,
  "perceived_bias_score": <float between 0.0 and 1.0>,
  "audit_findings": [<list of observations regarding demographic invariance>],
  "proxy_tokens_detected": [<list of location, name, or cultural proxy tokens>],
  "recommendation": "<recommendation on whether redaction or reranking is necessary>"
}
"""


def build_scoring_user_prompt(job_description: str, resume_text: str) -> str:
    return f"""JOB DESCRIPTION:
{job_description}

---
CANDIDATE RESUME:
{resume_text}

Assess the candidate against the job description and return the JSON evaluation.
"""


def build_audit_user_prompt(job_description: str, base_resume: str, variants_summary: str) -> str:
    return f"""JOB DESCRIPTION:
{job_description}

---
BASE RESUME:
{base_resume}

---
COUNTERFACTUAL VARIANTS TESTED:
{variants_summary}

Analyze demographic sensitivity and proxy risks, then output the JSON report.
"""
