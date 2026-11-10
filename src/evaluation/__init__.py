"""Evaluation Metrics and Fairness Audit Package (Stage 6)."""

from src.evaluation.metrics import (
    compute_ndcg_at_k,
    compute_mrr,
    compute_recall_at_k,
    compute_idcg,
    evaluate_query_pool,
)
from src.evaluation.disparity import (
    compute_group_exposure_summaries,
    audit_demographic_disparity,
)
from src.evaluation.hypotheses import (
    apply_holm_bonferroni,
    evaluate_h1,
    evaluate_h5,
)

__all__ = [
    "compute_ndcg_at_k",
    "compute_mrr",
    "compute_recall_at_k",
    "compute_idcg",
    "evaluate_query_pool",
    "compute_group_exposure_summaries",
    "audit_demographic_disparity",
    "apply_holm_bonferroni",
    "evaluate_h1",
    "evaluate_h5",
]
