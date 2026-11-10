"""Experiment 05: Stage 4 Fairness Mitigation Evaluation (Greedy Reranker vs Baseline).

Compares:
1. Baseline Frozen Scorer
2. Redacted Scorer
3. Greedy Exposure-Aware Reranker (optimizing Ut - lambda * Dt)
Verifies the 2% relative nDCG loss constraint.
"""

from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.mitigation import RerankerCandidateInput
from src.contracts.ranking import RankedCandidate
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k
from src.evaluation.disparity import audit_demographic_disparity


def main():
    print("=" * 60)
    print("STAGE 4: MITIGATION EVALUATION (GREEDY RERANKER VS BASELINE)")
    print("=" * 60)

    # Synthetic baseline scores with subtle group bias
    candidates_data = [
        {"id": "c1", "group": IntersectionalGroup.WHITE_MALE, "grade": 2, "score": 0.88},
        {"id": "c2", "group": IntersectionalGroup.WHITE_FEMALE, "grade": 2, "score": 0.86},
        {"id": "c3", "group": IntersectionalGroup.BLACK_MALE, "grade": 2, "score": 0.84},
        {"id": "c4", "group": IntersectionalGroup.BLACK_FEMALE, "grade": 2, "score": 0.83},
        {"id": "c5", "group": IntersectionalGroup.WHITE_MALE, "grade": 1, "score": 0.75},
        {"id": "c6", "group": IntersectionalGroup.WHITE_FEMALE, "grade": 1, "score": 0.73},
        {"id": "c7", "group": IntersectionalGroup.BLACK_MALE, "grade": 1, "score": 0.70},
        {"id": "c8", "group": IntersectionalGroup.BLACK_FEMALE, "grade": 1, "score": 0.69},
        {"id": "c9", "group": IntersectionalGroup.WHITE_MALE, "grade": 0, "score": 0.45},
        {"id": "c10", "group": IntersectionalGroup.BLACK_MALE, "grade": 0, "score": 0.40},
    ]

    raw_scores = [c["score"] for c in candidates_data]
    norm_scores = compute_min_max_normalized_scores(raw_scores)

    inputs = [
        RerankerCandidateInput(
            variant_id=c["id"],
            base_resume_id=c["id"],
            group=c["group"],
            frozen_score=c["score"],
            normalized_score=norm_scores[idx],
            relevance_grade=c["grade"],
            tie_breaker_id=c["id"],
        )
        for idx, c in enumerate(candidates_data)
    ]

    # 1. Unmitigated Baseline
    sorted_base = sorted(inputs, key=lambda x: (-x.frozen_score, x.tie_breaker_id))
    base_ranked = [
        RankedCandidate(
            variant_id=c.variant_id,
            base_resume_id=c.base_resume_id,
            group=c.group,
            relevance_grade=RelevanceLabel(c.relevance_grade),
            raw_score=c.frozen_score,
            normalized_score=c.normalized_score,
            rank=idx + 1,
            exposure_at_10=RankedCandidate.calculate_exposure(idx + 1, 10),
        )
        for idx, c in enumerate(sorted_base)
    ]

    base_ndcg = compute_ndcg_at_k(base_ranked, 10)
    base_disp = audit_demographic_disparity(base_ranked)

    print(f"BASELINE: nDCG@10 = {base_ndcg:.4f}, BW Abs Gap = {base_disp.black_white_abs_exposure_gap:.4f}")

    # 2. Reranker with different lambda
    for lam in [0.1, 1.0, 5.0]:
        reranked = run_greedy_exposure_reranking(inputs, lambda_penalty=lam, cutoff_k=10)
        mit_ranked = [
            RankedCandidate(
                variant_id=r.variant_id,
                base_resume_id=r.base_resume_id,
                group=r.group,
                relevance_grade=RelevanceLabel(r.relevance_grade),
                raw_score=r.normalized_score,
                normalized_score=r.normalized_score,
                rank=r.reranked_rank,
                exposure_at_10=RankedCandidate.calculate_exposure(r.reranked_rank, 10),
            )
            for r in reranked
        ]
        mit_ndcg = compute_ndcg_at_k(mit_ranked, 10)
        mit_disp = audit_demographic_disparity(mit_ranked)
        rel_loss = ((base_ndcg - mit_ndcg) / base_ndcg) * 100.0 if base_ndcg > 0 else 0.0
        gap_reduction = (
            ((base_disp.black_white_abs_exposure_gap - mit_disp.black_white_abs_exposure_gap) / base_disp.black_white_abs_exposure_gap) * 100.0
            if base_disp.black_white_abs_exposure_gap > 0 else 0.0
        )

        print(f"\nRERANKER (lambda={lam}):")
        print(f"  nDCG@10: {mit_ndcg:.4f} (Relative loss: {rel_loss:.2f}% | Limit <= 2.0%)")
        print(f"  BW Abs Gap: {mit_disp.black_white_abs_exposure_gap:.4f} (Reduction: {gap_reduction:.2f}%)")
        print(f"  Passes 2% utility tolerance: {rel_loss <= 2.0}")


if __name__ == "__main__":
    main()
