"""Component view for Interactive Pareto Frontier & Utility-Fairness Trade-off Analysis."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.ranking import RankedCandidate
from src.contracts.mitigation import RerankerCandidateInput
from src.models.bm25_ranker import BM25Ranker
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k
from src.evaluation.disparity import audit_demographic_disparity


def render_pareto_view():
    """Renders Tab 2: Interactive Pareto Frontier Simulation."""
    st.subheader("⚖️ Utility vs. Fairness Pareto Frontier")
    st.caption("Empirical simulation exploring the optimal balance between ranking accuracy (nDCG@10) and demographic parity across penalty weights (λ).")

    if "last_run" not in st.session_state:
        st.info("💡 Please execute a ranking run on Tab 1 first to initialize the candidate pool and job description.")
        return

    data = st.session_state["last_run"]
    candidates = data["candidates_pool"]
    job_desc = data["job_desc"]
    cutoff_k = data["cutoff_k"]

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        lam_max = st.slider("Maximum Penalty λ:", min_value=1.0, max_value=8.0, value=4.0, step=0.5)
    with col2:
        num_steps = st.slider("Grid Resolution (Steps):", min_value=5, max_value=25, value=15, step=5)
    with col3:
        st.write("")
        st.write("")
        run_sweep = st.button("🔄 Compute Pareto Frontier", type="primary", use_container_width=True)

    if run_sweep or "pareto_cache" not in st.session_state:
        with st.spinner("Computing trade-off frontier across lambda grid..."):
            texts = [f"Candidate: {c['name']}\n\n{c['resume']}" for c in candidates]
            scorer = BM25Ranker()
            raw_scores = scorer.score_candidates(job_desc, texts)
            norm_scores = compute_min_max_normalized_scores(raw_scores)

            reranker_inputs = [
                RerankerCandidateInput(
                    variant_id=f"{c['id']}::var",
                    base_resume_id=c["id"],
                    group=c["group"],
                    frozen_score=raw_scores[idx],
                    normalized_score=norm_scores[idx],
                    relevance_grade=int(c["label"]),
                    tie_breaker_id=c["id"],
                )
                for idx, c in enumerate(candidates)
            ]

            grid = np.linspace(0.0, lam_max, num_steps)
            records = []
            base_ndcg = None

            for lam in grid:
                reranked = run_greedy_exposure_reranking(
                    candidates=reranker_inputs,
                    lambda_penalty=float(lam),
                    cutoff_k=cutoff_k,
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
                        exposure_at_10=RankedCandidate.calculate_exposure(ro.reranked_rank, cutoff_k),
                    )
                    for ro in reranked
                ]
                ndcg = compute_ndcg_at_k(ranked_items, cutoff_k)
                disparity = audit_demographic_disparity(ranked_items, cutoff_k=cutoff_k)

                if base_ndcg is None:
                    base_ndcg = ndcg

                utility_retention = (ndcg / base_ndcg) * 100 if base_ndcg > 0 else 100.0

                records.append({
                    "lambda": round(float(lam), 2),
                    "ndcg_at_10": round(float(ndcg), 4),
                    "utility_retention": round(utility_retention, 2),
                    "bw_gap": round(float(disparity.black_white_abs_exposure_gap), 4),
                    "fm_gap": round(float(disparity.female_male_abs_exposure_gap), 4),
                    "intersectional_excess": round(float(disparity.intersectional_excess), 4),
                })

            st.session_state["pareto_cache"] = records

    df_pareto = pd.DataFrame(st.session_state["pareto_cache"])

    # Highlight Optimal Balance (Criterion H2: Retains >= 98% utility while minimizing disparity)
    safe_points = df_pareto[df_pareto["utility_retention"] >= 98.0]
    optimal_point = safe_points.sort_values(by="bw_gap").iloc[0] if not safe_points.empty else df_pareto.iloc[0]

    st.markdown("### 📈 Interactive Pareto Trade-off Curve")
    fig = px.scatter(
        df_pareto,
        x="bw_gap",
        y="ndcg_at_10",
        color="lambda",
        size="utility_retention",
        hover_data=["lambda", "utility_retention", "fm_gap", "intersectional_excess"],
        labels={
            "bw_gap": "Fairness: Black-White Exposure Disparity Gap (Lower is Fairer)",
            "ndcg_at_10": "Utility: nDCG@10 (Higher is Better)",
            "lambda": "Penalty λ",
        },
        title="Pareto Trade-Off: Ranking Utility vs. Algorithmic Disparity Gap",
    )
    # Add optimal recommendation star
    fig.add_trace(
        go.Scatter(
            x=[optimal_point["bw_gap"]],
            y=[optimal_point["ndcg_at_10"]],
            mode="markers+text",
            marker=dict(symbol="star", size=18, color="#ef4444"),
            name="Optimal Point (H2 Compliant)",
            text=["⭐ Recommended λ"],
            textposition="top center",
        )
    )
    fig.update_layout(height=480, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Recommendation Callout
    st.success(
        f"**Algorithm Recommendation:** Optimal operating parameter is **λ = {optimal_point['lambda']}**. "
        f"It preserves **{optimal_point['utility_retention']}%** of baseline utility (nDCG@10: {optimal_point['ndcg_at_10']}) "
        f"while reducing the Black-White exposure gap to **{optimal_point['bw_gap']}**."
    )

    with st.expander("📋 View Complete Pareto Evaluation Table"):
        st.dataframe(df_pareto, use_container_width=True)
