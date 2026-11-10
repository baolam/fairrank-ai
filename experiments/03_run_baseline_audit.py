"""Experiment 03: Stage 3 & 6 Baseline Retrieval & Demographic Audit (H1, H5).

Runs BM25 and evaluates nDCG@10, exposure disparity, within-group noise floor,
and confirmatory hypotheses H1 and H5.
"""

from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.ranking import RankedCandidate
from src.models.bm25_ranker import BM25Ranker
from src.mitigation.greedy_reranker import compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k, compute_mrr
from src.evaluation.disparity import audit_demographic_disparity
from src.evaluation.hypotheses import evaluate_h1, evaluate_h5, apply_holm_bonferroni


def main():
    print("=" * 60)
    print("STAGE 3 & 6: BASELINE SCORING & AUDIT (H1, H5)")
    print("=" * 60)

    job_query = "Senior Python Backend Engineer with Docker and FastAPI experience."
    candidates = [
        {"name": "Lakisha Washington", "group": IntersectionalGroup.BLACK_FEMALE, "grade": RelevanceLabel.GOOD_FIT, "text": "Senior Python developer with Docker, FastAPI, and PostgreSQL."},
        {"name": "Jamal Washington", "group": IntersectionalGroup.BLACK_MALE, "grade": RelevanceLabel.GOOD_FIT, "text": "Python engineer with strong API development and Docker."},
        {"name": "Emily Miller", "group": IntersectionalGroup.WHITE_FEMALE, "grade": RelevanceLabel.GOOD_FIT, "text": "Senior software engineer specializing in Python and cloud services."},
        {"name": "Brad Miller", "group": IntersectionalGroup.WHITE_MALE, "grade": RelevanceLabel.GOOD_FIT, "text": "Experienced Python backend engineer with FastAPI and Docker."},
        {"name": "Ebony Williams", "group": IntersectionalGroup.BLACK_FEMALE, "grade": RelevanceLabel.POTENTIAL_FIT, "text": "Junior developer with basic Python and JavaScript experience."},
        {"name": "Tyrone Williams", "group": IntersectionalGroup.BLACK_MALE, "grade": RelevanceLabel.POTENTIAL_FIT, "text": "Software tester with some Python automation background."},
        {"name": "Sarah McCarthy", "group": IntersectionalGroup.WHITE_FEMALE, "grade": RelevanceLabel.POTENTIAL_FIT, "text": "Frontend engineer learning Python backend services."},
        {"name": "Douglas Meyer", "group": IntersectionalGroup.WHITE_MALE, "grade": RelevanceLabel.POTENTIAL_FIT, "text": "Full stack engineer with general Python knowledge."},
        {"name": "Shaniqua Harris", "group": IntersectionalGroup.BLACK_FEMALE, "grade": RelevanceLabel.NO_FIT, "text": "Digital marketing and social media campaign specialist."},
        {"name": "Darnell Jefferson", "group": IntersectionalGroup.BLACK_MALE, "grade": RelevanceLabel.NO_FIT, "text": "Customer service associate with inventory skills."},
        {"name": "Claire Snyder", "group": IntersectionalGroup.WHITE_FEMALE, "grade": RelevanceLabel.NO_FIT, "text": "Accounting manager with audit experience."},
        {"name": "Todd Sullivan", "group": IntersectionalGroup.WHITE_MALE, "grade": RelevanceLabel.NO_FIT, "text": "High school chemistry educator and science teacher."},
    ]

    corpus = [f"Candidate: {c['name']}\n\n{c['text']}" for c in candidates]
    ranker = BM25Ranker()
    scores = ranker.score_candidates(job_query, corpus)
    norm_scores = compute_min_max_normalized_scores(scores)

    sorted_indices = sorted(range(len(candidates)), key=lambda i: (-scores[i], i))

    ranked_candidates = []
    for rank_idx, idx in enumerate(sorted_indices, start=1):
        c = candidates[idx]
        exp = RankedCandidate.calculate_exposure(rank_idx, cutoff_k=10)
        ranked_candidates.append(
            RankedCandidate(
                variant_id=f"c_{idx}",
                base_resume_id=f"res_{idx}",
                group=c["group"],
                relevance_grade=c["grade"],
                raw_score=scores[idx],
                normalized_score=norm_scores[idx],
                rank=rank_idx,
                exposure_at_10=exp,
            )
        )

    ndcg_10 = compute_ndcg_at_k(ranked_candidates, cutoff_k=10)
    mrr_val = compute_mrr(ranked_candidates)
    disparity = audit_demographic_disparity(ranked_candidates, within_group_noise_floor_val=0.005)

    print(f"Utility: nDCG@10 = {ndcg_10:.4f}, MRR = {mrr_val:.4f}")
    print(f"Demographic Exposure Disparity:")
    print(f"  Black-White Signed Gap   : {disparity.black_white_signed_exposure_gap:+.4f}")
    print(f"  Black-White Absolute Gap : {disparity.black_white_abs_exposure_gap:.4f}")
    print(f"  Noise Floor              : {disparity.within_group_noise_floor:.4f}")
    print(f"  Cross-Group Excess       : {disparity.cross_group_excess:+.4f}")
    print(f"  Max Intersectional Gap   : {disparity.max_intersectional_gap:.4f}")
    print(f"  Intersectional Excess    : {disparity.intersectional_excess:+.4f}")

    # Evaluate Hypotheses
    h1_res = evaluate_h1(disparity.black_white_abs_exposure_gap, disparity.within_group_noise_floor)
    h5_res = evaluate_h5(disparity.intersectional_excess)

    adj_p = apply_holm_bonferroni([h1_res.p_value_raw, h5_res.p_value_raw])
    h1_res = h1_res.model_copy(update={"p_value_holm_adjusted": adj_p[0]})
    h5_res = h5_res.model_copy(update={"p_value_holm_adjusted": adj_p[1]})

    print("\nHypothesis Testing Results (Holm-adjusted):")
    print(f"  H1: supported={h1_res.is_supported}, point_est={h1_res.point_estimate:.4f}, p_adj={h1_res.p_value_holm_adjusted:.4e}")
    print(f"  H5: supported={h5_res.is_supported}, point_est={h5_res.point_estimate:.4f}, p_adj={h5_res.p_value_holm_adjusted:.4e}")


if __name__ == "__main__":
    main()
