"""Router for candidate retrieval, ranking, and fair exposure-aware reranking."""

from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, HTTPException, Depends
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.ranking import RankedCandidate
from src.contracts.mitigation import RerankerCandidateInput
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k, compute_mrr
from src.evaluation.disparity import audit_demographic_disparity
from src.api.dependencies import get_bm25_ranker, get_sbert_ranker

router = APIRouter(prefix="/api/v1/ranking", tags=["Ranking & Reranking"])


class CandidateInputSchema(BaseModel):
    id: str
    name: str = "Anonymous"
    text: str
    group: Union[IntersectionalGroup, str] = IntersectionalGroup.WHITE_MALE
    relevance_grade: int = Field(default=1, ge=0, le=2)

    @field_validator("group", mode="before")
    @classmethod
    def normalize_group(cls, v: Any) -> IntersectionalGroup:
        if isinstance(v, IntersectionalGroup):
            return v
        if isinstance(v, str):
            clean = v.strip().replace(" ", "_")
            for member in IntersectionalGroup:
                if member.value.lower() == clean.lower() or member.name.lower() == clean.lower():
                    return member
        return IntersectionalGroup.WHITE_MALE


class RankingRequestSchema(BaseModel):
    job_description: str
    candidates: List[CandidateInputSchema]
    model_name: str = "bm25"  # bm25 or sbert
    redaction_enabled: bool = False
    lambda_penalty: Optional[float] = None  # If set > 0, performs fair reranking
    cutoff_k: int = 10


class RankedCandidateOutputSchema(BaseModel):
    rank: int
    candidate_id: str
    candidate_name: str
    group: str
    raw_score: float
    normalized_score: float
    exposure_at_k: float
    relevance_grade: int


class GroupSummaryOutputSchema(BaseModel):
    group: str
    candidate_count: int
    mean_exposure_at_10: float
    selection_rate_at_10: float


class RankingResponseSchema(BaseModel):
    ranked_candidates: List[RankedCandidateOutputSchema]
    ndcg_at_k: float
    mrr: float
    black_white_exposure_gap: float
    female_male_exposure_gap: float
    intersectional_excess: float
    noise_floor: float
    cross_group_excess: float
    group_summaries: List[GroupSummaryOutputSchema]


@router.post("/execute", response_model=RankingResponseSchema)
def execute_ranking_pipeline(req: RankingRequestSchema):
    """Executes candidate scoring, optional fair reranking, and demographic audit."""
    if not req.candidates:
        raise HTTPException(status_code=400, detail="Candidate list cannot be empty.")

    # 1. Prepare text inputs with optional redaction
    processed_texts = []
    for c in req.candidates:
        if req.redaction_enabled:
            processed_texts.append(f"[CANDIDATE_NAME]\n\n{c.text}")
        else:
            processed_texts.append(f"Candidate: {c.name}\n\n{c.text}")

    # 2. Score candidates
    if req.model_name.lower() == "sbert":
        try:
            scorer = get_sbert_ranker()
            raw_scores = scorer.score_candidates(req.job_description, processed_texts)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"SBERT scoring error: {str(e)}")
    else:
        scorer = get_bm25_ranker()
        raw_scores = scorer.score_candidates(req.job_description, processed_texts)

    norm_scores = compute_min_max_normalized_scores(raw_scores)

    # 3. Rerank or Standard Sort
    if req.lambda_penalty is not None and req.lambda_penalty > 0:
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
        reranked_outputs = run_greedy_exposure_reranking(
            candidates=reranker_inputs,
            lambda_penalty=req.lambda_penalty,
            cutoff_k=req.cutoff_k,
        )
        ranked_items = []
        for ro in reranked_outputs:
            c_info = next(c for c in req.candidates if c.id == ro.base_resume_id)
            exp = RankedCandidate.calculate_exposure(ro.reranked_rank, req.cutoff_k)
            ranked_items.append(
                RankedCandidate(
                    variant_id=ro.variant_id,
                    base_resume_id=ro.base_resume_id,
                    group=ro.group,
                    relevance_grade=RelevanceLabel(ro.relevance_grade),
                    raw_score=ro.normalized_score,
                    normalized_score=ro.normalized_score,
                    rank=ro.reranked_rank,
                    exposure_at_10=exp,
                )
            )
    else:
        sorted_pairs = sorted(
            zip(req.candidates, raw_scores, norm_scores),
            key=lambda x: (-x[1], x[0].id),
        )
        ranked_items = []
        for rank_idx, (c, raw_s, norm_s) in enumerate(sorted_pairs, start=1):
            exp = RankedCandidate.calculate_exposure(rank_idx, req.cutoff_k)
            ranked_items.append(
                RankedCandidate(
                    variant_id=f"{c.id}::var",
                    base_resume_id=c.id,
                    group=c.group,
                    relevance_grade=RelevanceLabel(c.relevance_grade),
                    raw_score=raw_s,
                    normalized_score=norm_s,
                    rank=rank_idx,
                    exposure_at_10=exp,
                )
            )

    # 4. Evaluation Metrics
    ndcg_val = compute_ndcg_at_k(ranked_items, req.cutoff_k)
    mrr_val = compute_mrr(ranked_items)
    disparity = audit_demographic_disparity(ranked_items, cutoff_k=req.cutoff_k)

    # 5. Format response
    cand_lookup = {c.id: c for c in req.candidates}
    outputs = []
    for r in ranked_items:
        c_orig = cand_lookup.get(r.base_resume_id)
        outputs.append(
            RankedCandidateOutputSchema(
                rank=r.rank,
                candidate_id=r.base_resume_id,
                candidate_name=c_orig.name if not req.redaction_enabled else "[CANDIDATE_NAME]",
                group=r.group.value if r.group else "N/A",
                raw_score=float(r.raw_score),
                normalized_score=float(r.normalized_score),
                exposure_at_k=float(r.exposure_at_10),
                relevance_grade=int(r.relevance_grade),
            )
        )

    group_summaries = [
        GroupSummaryOutputSchema(
            group=group.value,
            candidate_count=summary.candidate_count,
            mean_exposure_at_10=float(summary.mean_exposure_at_10),
            selection_rate_at_10=float(summary.selection_rate_at_10),
        )
        for group, summary in disparity.group_summaries.items()
    ]

    return RankingResponseSchema(
        ranked_candidates=outputs,
        ndcg_at_k=float(ndcg_val),
        mrr=float(mrr_val),
        black_white_exposure_gap=float(disparity.black_white_abs_exposure_gap),
        female_male_exposure_gap=float(disparity.female_male_abs_exposure_gap),
        intersectional_excess=float(disparity.intersectional_excess),
        noise_floor=float(getattr(disparity, "within_group_noise_floor", 0.0)),
        cross_group_excess=float(disparity.cross_group_excess),
        group_summaries=group_summaries,
    )
