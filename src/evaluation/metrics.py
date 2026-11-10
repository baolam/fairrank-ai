"""Stage 3 & 6: Evaluation Metrics Implementation.

Computes:
- nDCG@k (Equation 1)
- MRR (Mean Reciprocal Rank for first Good Fit)
- Recall@k
- Exposure e_{qiv}(k) = 1(rank <= k) / log2(rank + 1)
"""

import math
from typing import List, Optional
from src.contracts.ranking import RankedCandidate
from src.contracts.raw_data import RelevanceLabel
from src.contracts.evaluation import QueryUtilityMetrics


def compute_idcg(labels: List[int], k: int) -> float:
    """Computes Ideal Discounted Cumulative Gain (IDCG) for top k positions."""
    sorted_labels = sorted(labels, reverse=True)
    idcg = 0.0
    for t in range(min(k, len(sorted_labels))):
        gain = (2.0 ** sorted_labels[t]) - 1.0
        discount = math.log2(t + 2)  # t=0 -> log2(2) = 1.0
        idcg += gain / discount
    return idcg


def compute_ndcg_at_k(ranked_candidates: List[RankedCandidate], cutoff_k: int = 10) -> float:
    """Computes nDCG@k strictly following Equation (1) of the proposal.

    For K_q = min(k, N_q):
        nDCG_q@k = [ sum_{t=1}^{K_q} (2^{l_t} - 1) / log2(t + 1) ] / IDCG_q@k
    """
    n_q = len(ranked_candidates)
    k_q = min(cutoff_k, n_q)
    if k_q == 0:
        return 0.0

    all_labels = [int(c.relevance_grade) for c in ranked_candidates]
    idcg = compute_idcg(all_labels, k_q)
    if idcg <= 1e-12:
        return 0.0

    dcg = 0.0
    for t in range(1, k_q + 1):
        cand = ranked_candidates[t - 1]
        gain = (2.0 ** int(cand.relevance_grade)) - 1.0
        discount = math.log2(t + 1)
        dcg += gain / discount

    return dcg / idcg


def compute_mrr(ranked_candidates: List[RankedCandidate]) -> float:
    """Mean Reciprocal Rank for the first Good Fit (grade 2). Zero if none exists."""
    for cand in ranked_candidates:
        if cand.relevance_grade == RelevanceLabel.GOOD_FIT:
            return 1.0 / cand.rank
    return 0.0


def compute_recall_at_k(ranked_candidates: List[RankedCandidate], cutoff_k: int = 10) -> Optional[float]:
    """Recall@k: count of Good Fit candidates in first K_q positions / total Good Fit candidates in pool.

    Undefined (None) if total Good Fit candidates == 0.
    """
    total_good_fit = sum(1 for c in ranked_candidates if c.relevance_grade == RelevanceLabel.GOOD_FIT)
    if total_good_fit == 0:
        return None

    k_q = min(cutoff_k, len(ranked_candidates))
    top_good_fit = sum(1 for c in ranked_candidates[:k_q] if c.relevance_grade == RelevanceLabel.GOOD_FIT)
    return top_good_fit / float(total_good_fit)


def evaluate_query_pool(
    job_id: str,
    ranked_candidates: List[RankedCandidate],
    cutoff_k: int = 10,
) -> QueryUtilityMetrics:
    """Computes comprehensive query utility metrics."""
    ndcg = compute_ndcg_at_k(ranked_candidates, cutoff_k)
    mrr_val = compute_mrr(ranked_candidates)
    rec_val = compute_recall_at_k(ranked_candidates, cutoff_k)
    all_labels = [int(c.relevance_grade) for c in ranked_candidates]
    idcg_val = compute_idcg(all_labels, min(cutoff_k, len(ranked_candidates)))

    return QueryUtilityMetrics(
        job_id=job_id,
        pool_size=len(ranked_candidates),
        ndcg_at_10=ndcg,
        mrr=mrr_val,
        recall_at_10=rec_val,
        ideal_dcg=idcg_val,
        has_good_fit=(rec_val is not None),
    )
