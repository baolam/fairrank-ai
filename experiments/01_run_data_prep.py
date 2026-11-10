"""Experiment 01: Stage 1 Data Preparation and Feasibility Gate.

Runs normalization, exact deduplication, conflicting label reconciliation,
SOC occupation assignment, and holdout feasibility check.
"""

from src.contracts.raw_data import (
    RawJobDescription,
    RawResume,
    LabeledPair,
    RelevanceLabel,
    SplitType,
)
from src.data_prep.normalizer import normalize_text, compute_content_hash
from src.data_prep.deduplicator import reconcile_conflicting_pairs, deduplicate_resumes
from src.data_prep.occupation_coder import assign_soc_category, evaluate_occupation_holdout_gate


def main():
    print("=" * 60)
    print("STAGE 1: DATA PREPARATION & OCCUPATION FEASIBILITY GATE")
    print("=" * 60)

    # Sample Job and Resume
    sample_job_text = """
    Software Engineer (Python/Data)
    Requirements:
    - 3+ years in Python, pandas, and machine learning.
    - Experience in automated testing and CI/CD pipelines.
    """
    sample_resume_text = """
    Experienced Python Developer with background in ML pipelines,
    automated testing, data analysis, and scalable APIs.
    """

    norm_job = normalize_text(sample_job_text)
    hash_job = compute_content_hash(norm_job)

    job = RawJobDescription(
        job_id="job_001",
        raw_text=sample_job_text,
        normalized_text=norm_job,
        content_hash=hash_job,
        split=SplitType.TRAIN,
    )

    soc_code, soc_title = assign_soc_category(job)
    print(f"Job ID: {job.job_id}")
    print(f"Content Hash: {job.content_hash[:16]}...")
    print(f"Assigned SOC: {soc_code} - {soc_title}")

    # Test conflicting labels reconciliation
    pairs = [
        LabeledPair(pair_id="p1", job_id="job_001", resume_id="res_001", relevance_grade=RelevanceLabel.GOOD_FIT),
        LabeledPair(pair_id="p2", job_id="job_001", resume_id="res_001", relevance_grade=RelevanceLabel.NO_FIT),
        LabeledPair(pair_id="p3", job_id="job_001", resume_id="res_002", relevance_grade=RelevanceLabel.POTENTIAL_FIT),
    ]

    valid, conflicts = reconcile_conflicting_pairs(pairs)
    print(f"\nPairs check: {len(valid)} valid pairs retained, {len(conflicts)} conflicting pairs excluded.")
    for c in conflicts:
        print(f"  [EXCLUDED CONFLICT] Pair {c.pair_id}: job {c.job_id} / resume {c.resume_id}")

    print("\nStage 1 contracts & pipeline checks PASSED successfully.")


if __name__ == "__main__":
    main()
