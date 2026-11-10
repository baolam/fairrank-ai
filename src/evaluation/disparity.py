"""Stage 3 & 6: Demographic Disparity and Fairness Audit.

Computes:
- Signed and absolute exposure gaps (Black vs White, Female vs Male)
- Within-group name-swap noise floor
- Cross-group excess
- Intersectional exposure gaps and excess (H5)
"""

from typing import List, Dict
import numpy as np
from src.contracts.ranking import RankedCandidate
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.evaluation import (
    DemographicExposureSummary,
    DisparityAuditResult,
)


def compute_group_exposure_summaries(
    candidates: List[RankedCandidate],
    cutoff_k: int = 10,
) -> Dict[IntersectionalGroup, DemographicExposureSummary]:
    """Calculates selection rates and mean exposure for each demographic group."""
    groups_data: Dict[IntersectionalGroup, List[float]] = {g: [] for g in IntersectionalGroup}
    selection_data: Dict[IntersectionalGroup, List[int]] = {g: [] for g in IntersectionalGroup}

    for c in candidates:
        if c.group in groups_data:
            groups_data[c.group].append(c.exposure_at_10)
            selection_data[c.group].append(1 if c.rank <= cutoff_k else 0)

    summaries: Dict[IntersectionalGroup, DemographicExposureSummary] = {}
    for g in IntersectionalGroup:
        exps = groups_data[g]
        sels = selection_data[g]
        count = len(exps)
        mean_exp = float(np.mean(exps)) if count > 0 else 0.0
        sel_rate = float(np.mean(sels)) if count > 0 else 0.0

        summaries[g] = DemographicExposureSummary(
            group=g,
            candidate_count=count,
            selection_rate_at_10=sel_rate,
            mean_exposure_at_10=mean_exp,
        )
    return summaries


def audit_demographic_disparity(
    candidates: List[RankedCandidate],
    within_group_noise_floor_val: float = 0.005,
    cutoff_k: int = 10,
) -> DisparityAuditResult:
    """Computes signed/absolute exposure gaps and intersectional contrast."""
    summaries = compute_group_exposure_summaries(candidates, cutoff_k)

    bf_exp = summaries[IntersectionalGroup.BLACK_FEMALE].mean_exposure_at_10
    bm_exp = summaries[IntersectionalGroup.BLACK_MALE].mean_exposure_at_10
    wf_exp = summaries[IntersectionalGroup.WHITE_FEMALE].mean_exposure_at_10
    wm_exp = summaries[IntersectionalGroup.WHITE_MALE].mean_exposure_at_10

    # Race contrast: equal weighting of gender strata
    black_mean = 0.5 * (bf_exp + bm_exp)
    white_mean = 0.5 * (wf_exp + wm_exp)
    bw_signed = black_mean - white_mean
    bw_abs = abs(bw_signed)

    # Gender contrast: equal weighting of race strata
    female_mean = 0.5 * (bf_exp + wf_exp)
    male_mean = 0.5 * (bm_exp + wm_exp)
    fm_signed = female_mean - male_mean
    fm_abs = abs(fm_signed)

    # Noise floor and excess
    excess = bw_abs - within_group_noise_floor_val

    # Intersectional contrasts (H5)
    all_exps = [bf_exp, bm_exp, wf_exp, wm_exp]
    max_inter = max(all_exps) - min(all_exps)
    max_marginal = max(bw_abs, fm_abs)
    inter_excess = max_inter - max_marginal

    return DisparityAuditResult(
        black_white_signed_exposure_gap=bw_signed,
        black_white_abs_exposure_gap=bw_abs,
        female_male_signed_exposure_gap=fm_signed,
        female_male_abs_exposure_gap=fm_abs,
        within_group_noise_floor=within_group_noise_floor_val,
        cross_group_excess=excess,
        max_intersectional_gap=max_inter,
        intersectional_excess=inter_excess,
        group_summaries=summaries,
    )
