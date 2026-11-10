"""Router for algorithmic bias auditing, counterfactual perturbation, and Pareto analysis."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.mitigation import RerankerCandidateInput
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k
from src.evaluation.disparity import audit_demographic_disparity
from src.contracts.ranking import RankedCandidate
from src.api.dependencies import get_bm25_ranker
from src.api.routers.ranking import CandidateInputSchema

router = APIRouter(prefix="/api/v1/audit", tags=["Auditing & Counterfactuals"])


class ParetoPoint(BaseModel):
    lambda_penalty: float
    ndcg_at_k: float
    black_white_exposure_gap: float
    female_male_exposure_gap: float
    intersectional_excess: float


class ParetoSweepRequest(BaseModel):
    job_description: str
    candidates: List[CandidateInputSchema]
    lambda_min: float = 0.0
    lambda_max: float = 4.0
    steps: int = 15
    cutoff_k: int = 10


class CounterfactualAuditRequest(BaseModel):
    job_description: str
    candidate_profile: str  # The pure resume body without name
    baseline_model: str = "bm25"


class GroupScoreSummary(BaseModel):
    group: str
    sample_names: List[str]
    mean_score: float
    score_variance: float
    scores: List[float]


class CounterfactualAuditResponse(BaseModel):
    candidate_profile_preview: str
    group_results: List[GroupScoreSummary]
    max_demographic_shift: float
    is_sensitive: bool
    redacted_group_results: List[GroupScoreSummary]
    mitigated_max_demographic_shift: float


# Canonical stimuli names per intersectional group (representative subset)
CANONICAL_AUDIT_STIMULI = {
    IntersectionalGroup.BLACK_FEMALE: ["Lakisha Washington", "Ebony Williams", "Shaniqua Harris", "Latoya Robinson"],
    IntersectionalGroup.BLACK_MALE: ["Jamal Washington", "Tyrone Williams", "Darnell Jefferson", "Trevon Davis"],
    IntersectionalGroup.WHITE_FEMALE: ["Emily Miller", "Sarah McCarthy", "Claire Snyder", "Laurie Krueger"],
    IntersectionalGroup.WHITE_MALE: ["Brad Miller", "Douglas Meyer", "Todd Sullivan", "Brett Baker"],
}


@router.post("/pareto-sweep", response_model=List[ParetoPoint])
def calculate_pareto_frontier(req: ParetoSweepRequest):
    """Calculates trade-off points between ranking utility and exposure parity across lambda grid."""
    if len(req.candidates) < 2:
        raise HTTPException(status_code=400, detail="Require at least 2 candidates to compute ranking metrics.")

    texts = [f"Candidate: {c.name}\n\n{c.text}" for c in req.candidates]
    scorer = get_bm25_ranker()
    raw_scores = scorer.score_candidates(req.job_description, texts)
    norm_scores = compute_min_max_normalized_scores(raw_scores)

    reranker_inputs = [
        RerankerCandidateInput(
            variant_id=f"{c.id}::var",
            base_resume_id=c.id,
            group=c.group,
            frozen_score=raw_scores[idx],
            normalized_score=norm_scores[idx],
            relevance_grade=c.relevance_grade,
            tie_breaker_id=c.id,
        )
        for idx, c in enumerate(req.candidates)
    ]

    import numpy as np
    lambda_grid = np.linspace(req.lambda_min, req.lambda_max, req.steps)
    points = []

    for lam in lambda_grid:
        reranked = run_greedy_exposure_reranking(
            candidates=reranker_inputs,
            lambda_penalty=float(lam),
            cutoff_k=req.cutoff_k,
        )
        ranked_items = [
            RankedCandidate(
                variant_id=ro.variant_id,
                base_resume_id=ro.base_resume_id,
                group=ro.group,
                relevance_grade=RelevanceLabel(ro.relevance_grade),
                raw_score=ro.normalized_score,
                normalized_score=ro.normalized_score,
                rank=ro.reranked_rank,
                exposure_at_10=RankedCandidate.calculate_exposure(ro.reranked_rank, req.cutoff_k),
            )
            for ro in reranked
        ]
        ndcg = compute_ndcg_at_k(ranked_items, req.cutoff_k)
        disparity = audit_demographic_disparity(ranked_items, cutoff_k=req.cutoff_k)

        points.append(
            ParetoPoint(
                lambda_penalty=round(float(lam), 3),
                ndcg_at_k=round(float(ndcg), 4),
                black_white_exposure_gap=round(float(disparity.black_white_abs_exposure_gap), 4),
                female_male_exposure_gap=round(float(disparity.female_male_abs_exposure_gap), 4),
                intersectional_excess=round(float(disparity.intersectional_excess), 4),
            )
        )

    return points


@router.post("/counterfactual", response_model=CounterfactualAuditResponse)
def run_counterfactual_audit(req: CounterfactualAuditRequest):
    """Perturbs candidate profile across demographic names and audits score variations."""
    scorer = get_bm25_ranker()
    group_results = []
    all_group_means = []

    for group, names in CANONICAL_AUDIT_STIMULI.items():
        variant_texts = [f"Candidate: {name}\n\n{req.candidate_profile}" for name in names]
        scores = scorer.score_candidates(req.job_description, variant_texts)
        mean_s = sum(scores) / len(scores) if scores else 0.0
        var_s = sum((s - mean_s) ** 2 for s in scores) / len(scores) if scores else 0.0

        all_group_means.append(mean_s)
        group_results.append(
            GroupScoreSummary(
                group=group.value,
                sample_names=names,
                mean_score=round(mean_s, 4),
                score_variance=round(var_s, 6),
                scores=[round(float(s), 6) for s in scores],
            )
        )

    max_shift = max(all_group_means) - min(all_group_means) if all_group_means else 0.0
    is_sensitive = max_shift > 0.001

    # Mitigated pipeline: redacted text is name-independent, so score it once per group
    # and reuse it across every injected name (mirrors the original demo's dual-pipeline audit).
    redacted_group_results = []
    redacted_group_means = []
    redacted_text = f"[CANDIDATE_NAME]\n\n{req.candidate_profile}"
    for group, names in CANONICAL_AUDIT_STIMULI.items():
        redacted_score = scorer.score_candidates(req.job_description, [redacted_text])[0]
        redacted_group_means.append(redacted_score)
        redacted_group_results.append(
            GroupScoreSummary(
                group=group.value,
                sample_names=names,
                mean_score=round(redacted_score, 4),
                score_variance=0.0,
                scores=[round(float(redacted_score), 6)] * len(names),
            )
        )
    mitigated_max_shift = (
        max(redacted_group_means) - min(redacted_group_means) if redacted_group_means else 0.0
    )

    return CounterfactualAuditResponse(
        candidate_profile_preview=req.candidate_profile[:160] + "...",
        group_results=group_results,
        max_demographic_shift=round(max_shift, 4),
        is_sensitive=is_sensitive,
        redacted_group_results=redacted_group_results,
        mitigated_max_demographic_shift=round(mitigated_max_shift, 4),
    )
