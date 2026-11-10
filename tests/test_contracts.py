"""Unit tests for Stage 1-6 Data Contracts."""

import pytest
from pydantic import ValidationError
from src.contracts.raw_data import LabeledPair, RelevanceLabel, RawResume, RawJobDescription, SplitType
from src.contracts.stimuli import DemographicName, PerceivedRace, PerceivedGender, IntersectionalGroup, StimulusPartition
from src.contracts.ranking import RankedCandidate
from src.contracts.mitigation import RerankerCandidateInput


def test_labeled_pair_contract():
    # Valid pair
    pair = LabeledPair(pair_id="p1", job_id="j1", resume_id="r1", relevance_grade=RelevanceLabel.GOOD_FIT)
    assert int(pair.relevance_grade) == 2

    # String mapping test
    pair_str = LabeledPair(pair_id="p2", job_id="j1", resume_id="r2", relevance_grade="potential fit")
    assert pair_str.relevance_grade == RelevanceLabel.POTENTIAL_FIT

    # Invalid grade should fail validation
    with pytest.raises(ValidationError):
        LabeledPair(pair_id="p3", job_id="j1", resume_id="r3", relevance_grade=5)


def test_ranked_candidate_exposure():
    # Rank 1: 1 / log2(2) = 1.0
    assert abs(RankedCandidate.calculate_exposure(1, 10) - 1.0) < 1e-6

    # Rank 3: 1 / log2(4) = 0.5
    assert abs(RankedCandidate.calculate_exposure(3, 10) - 0.5) < 1e-6

    # Rank 11 (> 10): exposure is 0.0
    assert RankedCandidate.calculate_exposure(11, 10) == 0.0


def test_stimuli_name_contract():
    name = DemographicName(
        name_id="n_01",
        full_name="Lakisha Washington",
        race=PerceivedRace.BLACK,
        gender=PerceivedGender.FEMALE,
        group=IntersectionalGroup.BLACK_FEMALE,
        partition=StimulusPartition.TEST,
        source="Test source",
    )
    assert name.race == PerceivedRace.BLACK
    assert name.partition == StimulusPartition.TEST
