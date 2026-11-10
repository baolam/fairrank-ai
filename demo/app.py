"""FairRank-AI: Enterprise Audit & Fairness-Aware Semantic Resume Ranking Platform.

Streamlit Dashboard demonstrating:
1. Live Resume Ingestion & Matching (PDF/DOCX/TXT Parser)
2. Interactive Utility-Fairness Pareto Frontier Simulator
3. Deep-Dive Counterfactual Bias Inspector (Identity Perturbation)
4. Official Compliance & Algorithmic Audit Report Center
"""

import streamlit as st
from src.contracts.stimuli import IntersectionalGroup
from src.contracts.raw_data import RelevanceLabel
from demo.components.ingestion_view import render_ingestion_and_ranking_view
from demo.components.pareto_view import render_pareto_view
from demo.components.counterfactual_view import render_counterfactual_view
from demo.components.report_view import render_report_view

st.set_page_config(
    page_title="FairRank-AI | Responsible AI Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Benchmark Balanced Candidate Pool (12 Audited Profiles)
DEFAULT_JOB = """Senior Full-Stack Software Engineer
We are seeking an experienced developer with 5+ years of experience in Python, distributed backend architectures, FastAPI, Docker, and PostgreSQL. Experience in modern web frameworks (React/Vue), cloud infrastructure (AWS/GCP), and CI/CD pipelines is strongly preferred."""

SAMPLE_CANDIDATES = [
    {
        "id": "cand_01",
        "name": "Lakisha Washington",
        "group": IntersectionalGroup.BLACK_FEMALE,
        "label": RelevanceLabel.GOOD_FIT,
        "resume": "Senior Python Developer with 6 years experience in scalable cloud services, Docker, FastAPI, and PostgreSQL. Built distributed microservices and managed CI/CD pipelines on AWS.",
    },
    {
        "id": "cand_02",
        "name": "Jamal Washington",
        "group": IntersectionalGroup.BLACK_MALE,
        "label": RelevanceLabel.GOOD_FIT,
        "resume": "Full-stack engineer with 5 years backend experience using Python, PostgreSQL, REST APIs, and Docker. Proficient in automated testing and GCP deployments.",
    },
    {
        "id": "cand_03",
        "name": "Emily Miller",
        "group": IntersectionalGroup.WHITE_FEMALE,
        "label": RelevanceLabel.GOOD_FIT,
        "resume": "Lead software engineer with 7 years specializing in Python backend systems, microservices, PostgreSQL, and cloud architecture on AWS. Mentored junior engineers.",
    },
    {
        "id": "cand_04",
        "name": "Brad Miller",
        "group": IntersectionalGroup.WHITE_MALE,
        "label": RelevanceLabel.GOOD_FIT,
        "resume": "Experienced Python developer with 6 years building distributed databases, FastAPI, Docker, and AWS deployments. Strong knowledge of system design.",
    },
    {
        "id": "cand_05",
        "name": "Ebony Williams",
        "group": IntersectionalGroup.BLACK_FEMALE,
        "label": RelevanceLabel.POTENTIAL_FIT,
        "resume": "Frontend developer with 4 years React experience and 1 year Python scripting. Familiar with Docker and PostgreSQL, seeking full-stack transition.",
    },
    {
        "id": "cand_06",
        "name": "Tyrone Williams",
        "group": IntersectionalGroup.BLACK_MALE,
        "label": RelevanceLabel.POTENTIAL_FIT,
        "resume": "Backend developer with 3 years experience in Python and Flask. Some exposure to PostgreSQL and Docker containers in development environments.",
    },
    {
        "id": "cand_07",
        "name": "Sarah McCarthy",
        "group": IntersectionalGroup.WHITE_FEMALE,
        "label": RelevanceLabel.POTENTIAL_FIT,
        "resume": "Junior software developer with 2 years Python and Django experience. Eager to expand into cloud infrastructure and distributed backend engineering.",
    },
    {
        "id": "cand_08",
        "name": "Douglas Meyer",
        "group": IntersectionalGroup.WHITE_MALE,
        "label": RelevanceLabel.POTENTIAL_FIT,
        "resume": "Software engineer with 3 years Python and SQL database experience. Good foundational knowledge of RESTful API development and Git.",
    },
    {
        "id": "cand_09",
        "name": "Shaniqua Harris",
        "group": IntersectionalGroup.BLACK_FEMALE,
        "label": RelevanceLabel.NO_FIT,
        "resume": "Digital marketing specialist and content strategist with 4 years managing social media campaigns, SEO, and Google Analytics. Basic HTML skills.",
    },
    {
        "id": "cand_10",
        "name": "Darnell Jefferson",
        "group": IntersectionalGroup.BLACK_MALE,
        "label": RelevanceLabel.NO_FIT,
        "resume": "Customer success representative with 5 years managing client accounts, CRM data entry, and sales communication. Excellent verbal skills.",
    },
    {
        "id": "cand_11",
        "name": "Claire Snyder",
        "group": IntersectionalGroup.WHITE_FEMALE,
        "label": RelevanceLabel.NO_FIT,
        "resume": "Financial accountant with CPA credentials and 4 years auditing corporate financial reports. Expert in Excel spreadsheets and QuickBooks.",
    },
    {
        "id": "cand_12",
        "name": "Todd Sullivan",
        "group": IntersectionalGroup.WHITE_MALE,
        "label": RelevanceLabel.NO_FIT,
        "resume": "High school science teacher with 6 years experience designing chemistry curricula and leading biology laboratory sessions.",
    },
]

# Sidebar Overview
st.sidebar.title("🛡️ FairRank-AI")
st.sidebar.caption("Enterprise Algorithmic Fairness & Audit Engine")
st.sidebar.markdown(
    """
    **Core Capabilities:**
    - ⚡ **Information Retrieval:** BM25, Sentence-BERT
    - ⚖️ **Mitigation:** Greedy Exposure-Aware Reranker, CDA
    - 🔍 **Causal Audit:** Counterfactual Invariance, PopResume PSE
    - 📑 **Compliance:** Holm-Bonferroni, EU AI Act Reporting
    """
)
st.sidebar.divider()
st.sidebar.markdown(
    """
    **Architecture & API:**
    - 🚀 **REST API Docs:** `http://localhost:8000/docs`
    - 🐳 **Dockerized:** Backend + Frontend Multi-service
    - 🧪 **Test Suite:** 11 Automated Tests Passing
    """
)

# Header Banner
st.title("🛡️ FairRank-AI: Enterprise Audit & Fairness-Aware Resume Ranking")
st.markdown(
    "An interactive AI auditing platform demonstrating **Algorithmic Accountability, Bias Mitigation, and Utility Preservation** "
    "in Automated Resume-Job Recommendation."
)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📁 Tab 1: Live Ingestion & Ranking",
    "⚖️ Tab 2: Pareto Frontier Simulator",
    "🔍 Tab 3: Counterfactual Bias Inspector",
    "📑 Tab 4: Compliance & Audit Report",
])

with tab1:
    render_ingestion_and_ranking_view(SAMPLE_CANDIDATES, DEFAULT_JOB)

with tab2:
    render_pareto_view()

with tab3:
    render_counterfactual_view()

with tab4:
    render_report_view()
