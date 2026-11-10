"""Standard Occupational Classification (SOC) coding and holdout feasibility gate (Stage 1).

Constraints:
- Codes job descriptions into SOC categories.
- Holdout category is the largest category with >= 20 eligible job queries.
- Occupation gate fails if no category meets 20-query criterion or fewer than 30 eligible in-domain test queries remain.
"""

from typing import List, Dict, Optional, Tuple
from collections import Counter
from src.contracts.raw_data import RawJobDescription


# SOC broad occupational categories dictionary
DEFAULT_SOC_MAP = {
    "15-0000": "Computer and Mathematical Occupations",
    "13-0000": "Business and Financial Operations Occupations",
    "25-0000": "Educational Instruction and Library Occupations",
    "29-0000": "Healthcare Practitioners and Technical Occupations",
    "47-0000": "Construction and Extraction Occupations",
    "11-0000": "Management Occupations",
    "41-0000": "Sales and Related Occupations",
}


def assign_soc_category(job: RawJobDescription, codebook: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
    """Matches job title and description text to SOC occupational category."""
    mapping = codebook or DEFAULT_SOC_MAP
    text_lower = job.normalized_text.lower()

    if any(k in text_lower for k in ["software", "developer", "engineer", "python", "data", "algorithm"]):
        return "15-0000", mapping.get("15-0000", "Computer and Mathematical")
    elif any(k in text_lower for k in ["accountant", "auditor", "finance", "financial", "tax"]):
        return "13-0000", mapping.get("13-0000", "Business and Financial")
    elif any(k in text_lower for k in ["nurse", "clinical", "hospital", "patient", "medical"]):
        return "29-0000", mapping.get("29-0000", "Healthcare")
    elif any(k in text_lower for k in ["teacher", "school", "elementary", "education", "curriculum"]):
        return "25-0000", mapping.get("25-0000", "Education")
    elif any(k in text_lower for k in ["construction", "carpenter", "mason", "laborer", "site"]):
        return "47-0000", mapping.get("47-0000", "Construction")
    elif any(k in text_lower for k in ["manager", "director", "executive", "lead"]):
        return "11-0000", mapping.get("11-0000", "Management")
    else:
        return "41-0000", mapping.get("41-0000", "Sales and Related")


def evaluate_occupation_holdout_gate(
    jobs_with_soc: List[RawJobDescription],
    min_holdout_queries: int = 20,
    min_indomain_test_queries: int = 30,
) -> Tuple[bool, Optional[str], Dict[str, int]]:
    """Evaluates the Stage 1 occupation holdout feasibility gate."""
    soc_counts = Counter([j.soc_code for j in jobs_with_soc if j.soc_code])

    # Find largest category with >= min_holdout_queries
    eligible_candidates = [
        (soc, count) for soc, count in soc_counts.items() if count >= min_holdout_queries
    ]

    if not eligible_candidates:
        return False, None, dict(soc_counts)

    # Sort descending by count, then by code for tie-breaking
    eligible_candidates.sort(key=lambda x: (-x[1], x[0]))
    selected_holdout_soc = eligible_candidates[0][0]

    # Calculate remaining queries for 70:15:15 in-domain split
    remaining_total = sum(count for soc, count in soc_counts.items() if soc != selected_holdout_soc)
    estimated_indomain_test = int(remaining_total * 0.15)

    gate_passed = estimated_indomain_test >= min_indomain_test_queries
    return gate_passed, selected_holdout_soc, dict(soc_counts)
