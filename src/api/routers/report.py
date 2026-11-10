"""Router for generating and exporting compliance audit reports."""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse
from src.contracts.stimuli import IntersectionalGroup
from src.evaluation.report_generator import generate_markdown_audit_report, generate_html_audit_report
from src.api.routers.ranking import RankingResponseSchema

router = APIRouter(prefix="/api/v1/report", tags=["Compliance Reports"])


class ReportExportRequest(BaseModel):
    job_title: str = "Senior Full-Stack Software Engineer"
    job_description: str
    model_name: str = "BM25 + Greedy Fair Reranker"
    mitigation_strategy: str = "Exposure-Aware Reranking"
    lambda_val: float = 1.0
    ranking_summary: RankingResponseSchema


class MockDisparitySummary:
    """Lightweight adapter for report generator."""
    def __init__(self, res: RankingResponseSchema):
        self.black_white_abs_exposure_gap = res.black_white_exposure_gap
        self.female_male_abs_exposure_gap = res.female_male_exposure_gap
        self.intersectional_excess = res.intersectional_excess
        self.noise_floor = res.noise_floor
        self.cross_group_excess = res.cross_group_excess

        class GroupObj:
            pass

        self.group_summaries = {}
        summary_by_group = {gs.group: gs for gs in res.group_summaries}
        for group in IntersectionalGroup:
            gs = summary_by_group.get(group.value)
            g = GroupObj()
            g.count = gs.candidate_count if gs else 0
            g.mean_exposure_at_10 = gs.mean_exposure_at_10 if gs else 0.0
            g.selection_rate_at_10 = gs.selection_rate_at_10 if gs else 0.0
            self.group_summaries[group] = g


@router.post("/markdown", response_class=PlainTextResponse)
def export_markdown_report(req: ReportExportRequest):
    """Exports compliance report as standard Markdown."""
    summary_adapter = MockDisparitySummary(req.ranking_summary)
    cands_dict = [c.dict() for c in req.ranking_summary.ranked_candidates]
    return generate_markdown_audit_report(
        job_title=req.job_title,
        job_description=req.job_description,
        model_name=req.model_name,
        mitigation_strategy=req.mitigation_strategy,
        lambda_val=req.lambda_val,
        ndcg_at_10=req.ranking_summary.ndcg_at_k,
        mrr=req.ranking_summary.mrr,
        disparity_summary=summary_adapter,
        ranked_candidates=cands_dict,
    )


@router.post("/html", response_class=HTMLResponse)
def export_html_report(req: ReportExportRequest):
    """Exports compliance report as standalone styled HTML."""
    summary_adapter = MockDisparitySummary(req.ranking_summary)
    cands_dict = [c.dict() for c in req.ranking_summary.ranked_candidates]
    return generate_html_audit_report(
        job_title=req.job_title,
        job_description=req.job_description,
        model_name=req.model_name,
        mitigation_strategy=req.mitigation_strategy,
        lambda_val=req.lambda_val,
        ndcg_at_10=req.ranking_summary.ndcg_at_k,
        mrr=req.ranking_summary.mrr,
        disparity_summary=summary_adapter,
        ranked_candidates=cands_dict,
    )
