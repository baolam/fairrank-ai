"""Deduplication and conflict resolution module (Stage 1).

Constraints:
- Exact normalized hashes identify repeated texts.
- Conflicting labels for the same normalized pair are excluded and logged.
- No unlabeled pair is assigned No Fit.
"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict
from src.contracts.raw_data import LabeledPair, RawResume, RawJobDescription


def reconcile_conflicting_pairs(pairs: List[LabeledPair]) -> Tuple[List[LabeledPair], List[LabeledPair]]:
    """Identifies and removes conflicting relevance grades for identical pair keys.

    Returns:
        (valid_pairs, excluded_conflicts)
    """
    pair_dict: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    for p in pairs:
        pair_dict[(p.job_id, p.resume_id)].add(int(p.relevance_grade))

    valid_pairs: List[LabeledPair] = []
    excluded_conflicts: List[LabeledPair] = []

    for p in pairs:
        key = (p.job_id, p.resume_id)
        if len(pair_dict[key]) > 1:
            excluded_conflicts.append(p)
        else:
            # Keep unique first occurrence if duplicates with same label exist
            if not any(v.job_id == p.job_id and v.resume_id == p.resume_id for v in valid_pairs):
                valid_pairs.append(p)

    return valid_pairs, excluded_conflicts


def deduplicate_resumes(resumes: List[RawResume]) -> Tuple[List[RawResume], Dict[str, str]]:
    """Deduplicates resumes based on exact content hash.

    Returns:
        (unique_resumes, duplicate_mapping: {orig_id -> canonical_id})
    """
    seen_hashes: Dict[str, str] = {}
    unique_resumes: List[RawResume] = []
    mapping: Dict[str, str] = {}

    for r in resumes:
        if r.content_hash in seen_hashes:
            mapping[r.resume_id] = seen_hashes[r.content_hash]
        else:
            seen_hashes[r.content_hash] = r.resume_id
            mapping[r.resume_id] = r.resume_id
            unique_resumes.append(r)

    return unique_resumes, mapping
