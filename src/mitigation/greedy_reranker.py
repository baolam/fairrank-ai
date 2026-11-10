"""Stage 4: Greedy Score-Exposure Reranker (Equation 3).

Optimizes:
    argmax_{candidate} (Delta U_t - lambda * Delta D_t)
Positions 1 to K_q are filled greedily.
Remaining positions follow descending frozen score.
Stable tie-breaking uses deterministic IDs without group or name info.
"""

import math
from typing import List, Dict
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.mitigation import (
    RerankerCandidateInput,
    RerankerCandidateOutput,
)


def compute_min_max_normalized_scores(raw_scores: List[float]) -> List[float]:
    """Min-max scales raw scores to [0, 1]. Sets all to 0.0 if scores coincide."""
    if not raw_scores:
        return []
    min_s = min(raw_scores)
    max_s = max(raw_scores)
    if abs(max_s - min_s) < 1e-9:
        return [0.0] * len(raw_scores)
    return [(s - min_s) / (max_s - min_s) for s in raw_scores]


def position_weight(t: int, cutoff_k: int = 10) -> float:
    """Discount weight w(t) = 1 / log2(t + 1) for t <= cutoff_k, else 0."""
    if 1 <= t <= cutoff_k:
        return 1.0 / math.log2(t + 1)
    return 0.0


def run_greedy_exposure_reranking(
    candidates: List[RerankerCandidateInput],
    lambda_penalty: float = 1.0,
    cutoff_k: int = 10,
) -> List[RerankerCandidateOutput]:
    """Greedily constructs fair ranking prefix of length K_q, appending remainder by frozen score."""
    n_total = len(candidates)
    k_q = min(cutoff_k, n_total)

    if n_total == 0:
        return []

    # Calculate group counts in pool
    group_counts: Dict[IntersectionalGroup, int] = {}
    for c in candidates:
        group_counts[c.group] = group_counts.get(c.group, 0) + 1

    groups_present = list(group_counts.keys())
    sum_w_total_prefix = sum(position_weight(t, cutoff_k) for t in range(1, k_q + 1))

    # Keep track of unselected candidates
    # Sort initially by frozen_score desc, then stable tie_breaker_id
    sorted_init = sorted(candidates, key=lambda c: (-c.frozen_score, c.tie_breaker_id))
    original_rank_map = {c.variant_id: idx + 1 for idx, c in enumerate(sorted_init)}

    selected: List[RerankerCandidateInput] = []
    unselected = list(sorted_init)

    # Prefix cumulative exposure per group and cumulative utility numerator
    group_exposure_sum: Dict[IntersectionalGroup, float] = {g: 0.0 for g in groups_present}
    utility_score_sum: float = 0.0
    total_w_filled: float = 0.0

    # Fill positions 1 to K_q greedily
    for pos in range(1, k_q + 1):
        w_t = position_weight(pos, cutoff_k)
        new_total_w = total_w_filled + w_t

        best_cand = None
        best_gain = -float("inf")
        best_cand_idx = -1

        for idx, cand in enumerate(unselected):
            cand_group = cand.group
            cand_score = cand.normalized_score

            # Prospective new utility
            prospective_util = (utility_score_sum + w_t * cand_score) / sum_w_total_prefix

            # Prospective disparity D(pi_t)
            prospective_disp = 0.0
            for g in groups_present:
                n_g = group_counts[g]
                g_exp = group_exposure_sum[g] + (w_t if g == cand_group else 0.0)
                term = (g_exp / n_g) - (new_total_w / n_total)
                prospective_disp += term * term

            objective = prospective_util - lambda_penalty * prospective_disp

            # Check if this candidate improves objective or has better tie breaker
            if objective > best_gain or (
                abs(objective - best_gain) < 1e-9 and (best_cand is None or cand.tie_breaker_id < best_cand.tie_breaker_id)
            ):
                best_gain = objective
                best_cand = cand
                best_cand_idx = idx

        # Commit selected candidate
        assert best_cand is not None
        selected.append(best_cand)
        unselected.pop(best_cand_idx)

        # Update prefix running accumulators
        group_exposure_sum[best_cand.group] += w_t
        utility_score_sum += w_t * best_cand.normalized_score
        total_w_filled = new_total_w

    # Remaining positions follow descending frozen score
    unselected.sort(key=lambda c: (-c.frozen_score, c.tie_breaker_id))
    final_ordered = selected + unselected

    # Construct final contract output
    output: List[RerankerCandidateOutput] = []
    for rank_idx, cand in enumerate(final_ordered, start=1):
        output.append(
            RerankerCandidateOutput(
                variant_id=cand.variant_id,
                base_resume_id=cand.base_resume_id,
                group=cand.group,
                relevance_grade=cand.relevance_grade,
                reranked_rank=rank_idx,
                original_rank=original_rank_map[cand.variant_id],
                normalized_score=cand.normalized_score,
                marginal_objective_gain=0.0,
            )
        )

    return output
