"""Unit tests for evaluation metrics (nDCG@10, MRR, Recall)."""

from src.contracts.ranking import RankedCandidate
from src.contracts.raw_data import RelevanceLabel
from src.evaluation.metrics import compute_ndcg_at_k, compute_mrr, compute_recall_at_k


def test_ndcg_perfect_ranking():
    # Ideal ranking of 3 candidates: grades [2, 1, 0]
    candidates = [
        RankedCandidate(variant_id="1", base_resume_id="1", group=None, relevance_grade=RelevanceLabel.GOOD_FIT, raw_score=0.9, normalized_score=1.0, rank=1, exposure_at_10=1.0),
        RankedCandidate(variant_id="2", base_resume_id="2", group=None, relevance_grade=RelevanceLabel.POTENTIAL_FIT, raw_score=0.7, normalized_score=0.5, rank=2, exposure_at_10=0.63),
        RankedCandidate(variant_id="3", base_resume_id="3", group=None, relevance_grade=RelevanceLabel.NO_FIT, raw_score=0.2, normalized_score=0.0, rank=3, exposure_at_10=0.5),
    ]

    ndcg = compute_ndcg_at_k(candidates, cutoff_k=10)
    assert abs(ndcg - 1.0) < 1e-6


def test_mrr_and_recall():
    candidates = [
        RankedCandidate(variant_id="1", base_resume_id="1", group=None, relevance_grade=RelevanceLabel.NO_FIT, raw_score=0.9, normalized_score=1.0, rank=1, exposure_at_10=1.0),
        RankedCandidate(variant_id="2", base_resume_id="2", group=None, relevance_grade=RelevanceLabel.GOOD_FIT, raw_score=0.7, normalized_score=0.5, rank=2, exposure_at_10=0.63),
    ]
    # First good fit is rank 2 -> MRR = 1/2 = 0.5
    assert abs(compute_mrr(candidates) - 0.5) < 1e-6
    # 1 Good Fit in top 10 out of 1 total -> Recall = 1.0
    assert abs(compute_recall_at_k(candidates, 10) - 1.0) < 1e-6
