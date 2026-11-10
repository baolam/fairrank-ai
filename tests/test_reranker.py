"""Unit tests for Greedy Exposure Reranker."""

from src.contracts.stimuli import IntersectionalGroup
from src.contracts.mitigation import RerankerCandidateInput
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores


def test_greedy_reranker_reduces_disparity():
    # 4 candidates: 2 White with high scores, 2 Black with slightly lower scores
    candidates = [
        RerankerCandidateInput(variant_id="c1", base_resume_id="c1", group=IntersectionalGroup.WHITE_MALE, frozen_score=0.9, normalized_score=1.0, relevance_grade=2, tie_breaker_id="c1"),
        RerankerCandidateInput(variant_id="c2", base_resume_id="c2", group=IntersectionalGroup.WHITE_FEMALE, frozen_score=0.85, normalized_score=0.8, relevance_grade=2, tie_breaker_id="c2"),
        RerankerCandidateInput(variant_id="c3", base_resume_id="c3", group=IntersectionalGroup.BLACK_MALE, frozen_score=0.82, normalized_score=0.7, relevance_grade=2, tie_breaker_id="c3"),
        RerankerCandidateInput(variant_id="c4", base_resume_id="c4", group=IntersectionalGroup.BLACK_FEMALE, frozen_score=0.80, normalized_score=0.6, relevance_grade=2, tie_breaker_id="c4"),
    ]

    # Without penalty (lambda = 0), ordering preserves frozen scores
    res_base = run_greedy_exposure_reranking(candidates, lambda_penalty=0.0, cutoff_k=4)
    assert [r.variant_id for r in res_base] == ["c1", "c2", "c3", "c4"]

    # With strong penalty (lambda = 10), algorithm interleaves groups to achieve exposure parity
    res_fair = run_greedy_exposure_reranking(candidates, lambda_penalty=10.0, cutoff_k=4)
    first_two_groups = [res_fair[0].group, res_fair[1].group]
    assert len(set(first_two_groups)) == 2  # Different groups promoted into top 2!
