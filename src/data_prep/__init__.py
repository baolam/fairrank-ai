"""Data preparation and partitioning package (Stage 1)."""

from src.data_prep.normalizer import normalize_text, compute_content_hash
from src.data_prep.deduplicator import reconcile_conflicting_pairs, deduplicate_resumes
from src.data_prep.occupation_coder import assign_soc_category, evaluate_occupation_holdout_gate
from src.data_prep.splitter import partition_jobs, build_cold_resume_test_pool

__all__ = [
    "normalize_text",
    "compute_content_hash",
    "reconcile_conflicting_pairs",
    "deduplicate_resumes",
    "assign_soc_category",
    "evaluate_occupation_holdout_gate",
    "partition_jobs",
    "build_cold_resume_test_pool",
]
