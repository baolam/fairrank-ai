"""Component view for Job Description & Resume Ingestion, Matching and Fair Ranking."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from src.contracts.ranking import RankedCandidate
from src.contracts.mitigation import RerankerCandidateInput
from src.models.bm25_ranker import BM25Ranker
from src.mitigation.greedy_reranker import run_greedy_exposure_reranking, compute_min_max_normalized_scores
from src.evaluation.metrics import compute_ndcg_at_k, compute_mrr
from src.evaluation.disparity import audit_demographic_disparity
from src.parser.document_loader import load_text_from_bytes
from src.parser.resume_extractor import extract_resume_entities


def render_ingestion_and_ranking_view(sample_candidates: List[Dict[str, Any]], default_job_desc: str):
    """Renders Tab 1: Live CV Ingestion, Automated Parsing, and Fairness-Aware Ranking."""
    st.subheader("🎯 Job Matching & Demographic Auditing")
    st.caption("Upload raw candidate files or choose standard test pools to evaluate algorithmic allocation.")

    col_jd, col_input = st.columns([1, 1])

    with col_jd:
        job_title = st.text_input("Target Job Title:", "Senior Full-Stack Software Engineer")
        job_desc = st.text_area("Job Description Requirements:", default_job_desc, height=180)

    with col_input:
        data_source = st.radio(
            "Select Candidate Source:",
            ["Balanced Audit Pool (12 Synthetic Profiles)", "Upload Custom Files (.pdf, .docx, .txt)"],
            horizontal=True,
        )

        candidates_pool = []
        if data_source == "Balanced Audit Pool (12 Synthetic Profiles)":
            candidates_pool = sample_candidates
            st.success(f"Loaded {len(sample_candidates)} audited profiles across 4 intersectional demographic groups.")
        else:
            uploaded_files = st.file_uploader(
                "Upload Resume Documents:",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="Supports direct PDF/DOCX text extraction with automated entity redaction.",
            )
            if uploaded_files:
                for idx, uf in enumerate(uploaded_files):
                    content = uf.read()
                    text = load_text_from_bytes(content, uf.name)
                    parsed = extract_resume_entities(text, filename_hint=uf.name)
                    # Assign round-robin demographic group for testing fairness impact
                    groups_list = list(IntersectionalGroup)
                    assigned_group = groups_list[idx % len(groups_list)]
                    candidates_pool.append({
                        "id": f"upload_{idx+1}",
                        "name": parsed.predicted_name or f"Candidate {idx+1}",
                        "group": assigned_group,
                        "label": RelevanceLabel.POTENTIAL_FIT,
                        "resume": parsed.raw_text,
                        "skills": parsed.skills,
                        "exp": parsed.years_of_experience,
                        "redacted_text": parsed.redacted_text,
                    })
                st.info(f"Successfully parsed {len(candidates_pool)} resume files.")
            else:
                st.warning("Please upload one or more files, or switch to the Balanced Audit Pool.")

    if not candidates_pool:
        return

    # Configuration Bar
    st.divider()
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        model_type = st.selectbox(
            "Ranking Engine:",
            ["BM25 (Lexical Baseline)", "Greedy Fair Reranker (Exposure-Aware)", "Sentence-BERT (all-mpnet-base-v2)"],
        )
    with c2:
        redaction = st.checkbox("🛡️ Enable Sensitive Redaction", value=False, help="Masks candidate names, emails, and phone proxies.")
    with c3:
        lambda_val = st.slider(
            "Fairness Penalty λ:",
            min_value=0.0,
            max_value=5.0,
            value=1.5 if "Rerank" in model_type else 0.0,
            step=0.1,
            help="Penalty weight enforcing demographic exposure parity (Eq. 3)",
        )
    with c4:
        cutoff_k = st.number_input("Top-K Cutoff:", min_value=1, max_value=20, value=min(10, len(candidates_pool)))

    if st.button("🚀 Run Ranking & Audit Pipeline", type="primary", use_container_width=True):
        # Prepare inputs
        texts = []
        for c in candidates_pool:
            if redaction:
                texts.append(f"[CANDIDATE_NAME]\n\n{c.get('redacted_text', c['resume'])}")
            else:
                texts.append(f"Candidate: {c['name']}\n\n{c['resume']}")

        # Score with selected model
        if "BM25" in model_type or "Rerank" in model_type:
            scorer = BM25Ranker()
            raw_scores = scorer.score_candidates(job_desc, texts)
        else:
            with st.spinner("Embedding and scoring with SBERT mpnet..."):
                from src.models.sbert_ranker import SBERTRanker
                scorer = SBERTRanker()
                raw_scores = scorer.score_candidates(job_desc, texts)

        norm_scores = compute_min_max_normalized_scores(raw_scores)

        # Rerank or Standard Sort
        if "Rerank" in model_type or lambda_val > 0:
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
                for idx, c in enumerate(candidates_pool)
            ]
            reranked_outputs = run_greedy_exposure_reranking(
                candidates=reranker_inputs,
                lambda_penalty=lambda_val,
                cutoff_k=cutoff_k,
            )
            ranked_items = []
            for ro in reranked_outputs:
                c_info = next(c for c in candidates_pool if c["id"] == ro.base_resume_id)
                exp = RankedCandidate.calculate_exposure(ro.reranked_rank, cutoff_k)
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
                zip(candidates_pool, raw_scores, norm_scores),
                key=lambda x: (-x[1], x[0]["id"]),
            )
            ranked_items = []
            for rank_idx, (c, raw_s, norm_s) in enumerate(sorted_pairs, start=1):
                exp = RankedCandidate.calculate_exposure(rank_idx, cutoff_k)
                ranked_items.append(
                    RankedCandidate(
                        variant_id=f"{c['id']}::var",
                        base_resume_id=c["id"],
                        group=c["group"],
                        relevance_grade=c["label"],
                        raw_score=raw_s,
                        normalized_score=norm_s,
                        rank=rank_idx,
                        exposure_at_10=exp,
                    )
                )

        # Compute evaluation metrics
        ndcg_val = compute_ndcg_at_k(ranked_items, cutoff_k)
        mrr_val = compute_mrr(ranked_items)
        disparity = audit_demographic_disparity(ranked_items, cutoff_k=cutoff_k)

        # Save to session state for Tab 2, 3, 4
        st.session_state["last_run"] = {
            "job_title": job_title,
            "job_desc": job_desc,
            "model_type": model_type,
            "lambda_val": lambda_val,
            "cutoff_k": cutoff_k,
            "ndcg": ndcg_val,
            "mrr": mrr_val,
            "disparity": disparity,
            "ranked_items": ranked_items,
            "candidates_pool": candidates_pool,
            "redaction": redaction,
        }

        # Metric Tiles
        st.markdown("### 📊 Ranking Performance & Algorithmic Parity")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Utility (nDCG@10)", f"{ndcg_val:.3f}")
        m2.metric("MRR", f"{mrr_val:.3f}")
        m3.metric("B-W Exp Gap", f"{disparity.black_white_abs_exposure_gap:.4f}")
        m4.metric("F-M Exp Gap", f"{disparity.female_male_abs_exposure_gap:.4f}")
        m5.metric("Intersectional Excess (H5)", f"{disparity.intersectional_excess:.4f}")

        # Candidates Table
        st.markdown("### 📋 Ranked Candidate Allocation")
        rows = []
        for r in ranked_items:
            cand_orig = next(c for c in candidates_pool if c["id"] == r.base_resume_id)
            rows.append({
                "Rank": r.rank,
                "Candidate Name": cand_orig["name"] if not redaction else "[CANDIDATE_NAME]",
                "Group": r.group.value if r.group else "N/A",
                "Relevance Grade": r.relevance_grade.name,
                "Score": f"{r.raw_score:.3f}",
                "Exposure e(k)": f"{r.exposure_at_10:.3f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # Group Distribution Chart
        st.markdown("### 📈 Group Allocation Breakdown")
        chart_df = pd.DataFrame([
            {
                "Group": g.value,
                "Mean Exposure": disparity.group_summaries[g].mean_exposure_at_10,
                "Selection Rate @ 10": disparity.group_summaries[g].selection_rate_at_10,
            }
            for g in IntersectionalGroup if g in disparity.group_summaries
        ]).set_index("Group")
        st.bar_chart(chart_df)
