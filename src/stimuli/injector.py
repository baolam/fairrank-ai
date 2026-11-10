"""Stage 2: Template-based Demographic Name Injector.

Constraints from proposal:
- Train template: top name line
- Val template: labeled contact header
- Test template: name line below summary
- Redaction: neutral token replacement
"""

from typing import Optional
from src.contracts.stimuli import (
    CandidateVariant,
    DemographicName,
    TemplateType,
)
from src.contracts.raw_data import RawResume


def render_candidate_variant(
    base_resume: RawResume,
    name: Optional[DemographicName] = None,
    template_type: TemplateType = TemplateType.TEST_BELOW_SUMMARY,
    neutral_token: str = "[CANDIDATE_NAME]",
) -> CandidateVariant:
    """Renders candidate resume variant using locked templates."""
    base_id = base_resume.resume_id
    body = base_resume.normalized_text

    if name is None or template_type == TemplateType.REDACTED_NEUTRAL:
        rendered_text = f"{neutral_token}\n\n{body}"
        return CandidateVariant(
            variant_id=f"{base_id}::redacted",
            base_resume_id=base_id,
            name_id=None,
            candidate_name=neutral_token,
            group=None,
            template_type=TemplateType.REDACTED_NEUTRAL,
            rendered_text=rendered_text,
            is_redacted=True,
        )

    cand_name = name.full_name
    variant_id = f"{base_id}::{name.name_id}"

    if template_type == TemplateType.TRAIN_TOP_LINE:
        rendered_text = f"{cand_name}\n\n{body}"
    elif template_type == TemplateType.VAL_CONTACT_HEADER:
        rendered_text = f"Applicant Name: {cand_name}\nContact: candidate@audit-study.org\n---\n{body}"
    elif template_type == TemplateType.TEST_BELOW_SUMMARY:
        rendered_text = f"PROFESSIONAL SUMMARY\nExperienced Candidate Profile\nCandidate: {cand_name}\n\n{body}"
    else:
        rendered_text = f"{cand_name}\n\n{body}"

    return CandidateVariant(
        variant_id=variant_id,
        base_resume_id=base_id,
        name_id=name.name_id,
        candidate_name=cand_name,
        group=name.group,
        template_type=template_type,
        rendered_text=rendered_text,
        is_redacted=False,
    )
