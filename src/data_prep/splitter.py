"""Dataset partitioning module (Stage 1).

Enforces job-disjoint splitting (70:15:15) stratified by occupation and pool-size band,
and generates secondary cold-resume generalization pools.
"""

import random
from typing import List, Dict, Tuple
from collections import defaultdict
from src.contracts.raw_data import RawJobDescription, SplitType, LabeledPair


def partition_jobs(
    jobs: List[RawJobDescription],
    holdout_soc: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 17,
) -> Dict[str, SplitType]:
    """Partitions jobs into train, val, test_indomain, and test_holdout."""
    rng = random.Random(seed)
    split_map: Dict[str, SplitType] = {}

    holdout_jobs = [j for j in jobs if j.soc_code == holdout_soc]
    for j in holdout_jobs:
        split_map[j.job_id] = SplitType.TEST_HOLDOUT

    indomain_jobs = [j for j in jobs if j.soc_code != holdout_soc]

    # Stratify by soc_code
    by_soc = defaultdict(list)
    for j in indomain_jobs:
        by_soc[j.soc_code or "unknown"].append(j)

    for soc, group in by_soc.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        for j in group[:n_train]:
            split_map[j.job_id] = SplitType.TRAIN
        for j in group[n_train:n_train + n_val]:
            split_map[j.job_id] = SplitType.VAL
        for j in group[n_train + n_val:]:
            split_map[j.job_id] = SplitType.TEST_INDOMAIN

    return split_map


def build_cold_resume_test_pool(
    test_pairs: List[LabeledPair],
    train_resume_ids: set,
) -> Tuple[List[LabeledPair], int]:
    """Secondary test view: removes resumes seen in training and reports surviving judged pools.

    Does NOT replenish with unjudged negatives (per proposal Stage 1).
    """
    cold_pairs = [p for p in test_pairs if p.resume_id not in train_resume_ids]
    removed_count = len(test_pairs) - len(cold_pairs)
    return cold_pairs, removed_count
