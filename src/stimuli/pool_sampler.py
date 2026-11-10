"""Stage 2: Deterministic Pool Composition Sampler.

Constructs balanced and 70:30 Black/White background name assignments for pools.
Constraints from proposal:
- Counterfactual variants do not coexist as duplicate candidates in one pool.
- Background names are assigned independently of relevance.
- Balanced setting uses approximately equal four-group representation.
- 70:30 allocation has equal gender shares within race (35% BF, 35% BM, 15% WF, 15% WM).
- Reversed control (15% BF, 15% BM, 35% WF, 35% WM).
"""

import random
from typing import List, Dict
from src.contracts.stimuli import DemographicName, IntersectionalGroup, StimulusPartition
from src.contracts.raw_data import RawResume


def assign_pool_demographics(
    candidates: List[RawResume],
    stimuli: List[DemographicName],
    composition_mode: str = "balanced",
    partition: StimulusPartition = StimulusPartition.TEST,
    seed: int = 17,
) -> Dict[str, DemographicName]:
    """Deterministically assigns one name from the appropriate partition to each base candidate."""
    rng = random.Random(seed)

    eligible_stimuli = [s for s in stimuli if s.partition == partition]
    by_group: Dict[IntersectionalGroup, List[DemographicName]] = {
        g: [s for s in eligible_stimuli if s.group == g] for g in IntersectionalGroup
    }

    n_total = len(candidates)
    if composition_mode == "balanced":
        # Equal share: 25% each
        weights = {g: 0.25 for g in IntersectionalGroup}
    elif composition_mode == "70_30_black":
        weights = {
            IntersectionalGroup.BLACK_FEMALE: 0.35,
            IntersectionalGroup.BLACK_MALE: 0.35,
            IntersectionalGroup.WHITE_FEMALE: 0.15,
            IntersectionalGroup.WHITE_MALE: 0.15,
        }
    elif composition_mode == "70_30_white":
        weights = {
            IntersectionalGroup.BLACK_FEMALE: 0.15,
            IntersectionalGroup.BLACK_MALE: 0.15,
            IntersectionalGroup.WHITE_FEMALE: 0.35,
            IntersectionalGroup.WHITE_MALE: 0.35,
        }
    else:
        raise ValueError(f"Unknown composition_mode: {composition_mode}")

    # Compute target counts per group
    target_counts = {g: int(round(w * n_total)) for g, w in weights.items()}

    # Adjust rounding differences to match exact total
    diff = n_total - sum(target_counts.values())
    if diff != 0:
        first_group = list(target_counts.keys())[0]
        target_counts[first_group] += diff

    # Create pool group assignments list
    pool_groups: List[IntersectionalGroup] = []
    for g, count in target_counts.items():
        pool_groups.extend([g] * count)

    rng.shuffle(pool_groups)

    assignments: Dict[str, DemographicName] = {}
    for cand, group in zip(candidates, pool_groups):
        avail_names = by_group[group]
        chosen_name = rng.choice(avail_names)
        assignments[cand.resume_id] = chosen_name

    return assignments
