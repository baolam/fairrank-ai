"""Stimuli and variant injection package (Stage 2)."""

from src.stimuli.manifest_builder import build_stimuli_manifest
from src.stimuli.injector import render_candidate_variant
from src.stimuli.pool_sampler import assign_pool_demographics

__all__ = [
    "build_stimuli_manifest",
    "render_candidate_variant",
    "assign_pool_demographics",
]
