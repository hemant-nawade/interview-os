"""
Interview OS — main Streamlit entry point.

Routing lives here; all page bodies live in components/*. Business logic
(question generation, evaluation, adaptive difficulty, reports) lives in
services/*, so this file should never grow LLM prompts or SQL.
"""
from __future__ import annotations

import streamlit as st

from components.dashboard import dashboard
from components.interview import interview_ui, results, setup
from database.database import get_interview_full, get_or_create_user, init_db
from services.report_generator import build_report_pdf
from utils.config import settings

st.set_page_config(page_title="Interview OS", page_icon="🎯", layout="wide")

# ---------------------------------------------------------------- styling --
st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at 20% -10%, #1e1b4b 0%, #020617 45%); }
    section[data-testid="stSidebar"] { background: #0b1120; }
    h1, h2, h3, h4 { color: #f8fafc !important; }
    p, li, label, .stMarkdown { color: #cbd5e1; }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04); border: 1px solid #1e293b;
        border-radius: 14px; padding: 10px 14px;
    }
    .stButton>button {
        border-radius: 10px; font-weight: 600;
    }
    .feature-card {
        background: rgba(255,255,255,0.04); border: 1px solid #1e293b;
        border-radius: 16px; padding: 20px; height: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user_id" not in st.session_state:
    st.session_state.user_id = get_or_create_user("Candidate")
if "interview_state" not in st.session_state:
    st.session_state.interview_state = None


def _sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🎯 Interview OS")
        st.caption("Your AI interviewer")
        if not settings.llm_enabled:
            st.warning("No ANTHROPIC_API_KEY set — interviews are disabled until .env is configured.", icon="⚠️")
        st.divider()
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()
        if st.button("🎤 Start Interview", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()


def _landing() -> None:
    st.markdown(
        """
        <div style="text-align:center; padding: 60px 0 20px;">
            <h1 style="font-size:52px;">Practice Interviews. <span style="color:#818cf8;">Get Hired.</span></h1>
            <p style="font-size:19px; color:#94a3b8; max-width:640px; margin:0 auto;">
                Your AI interviewer that asks, listens, evaluates, and tells you exactly how to improve.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        cc1, cc2 = st.columns(2)
        if cc1.button("Start Interview", type="primary", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()
        if cc2.button("View Demo", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    features = [
        ("🧠", "AI-Powered Questions", "Every question is generated live by an LLM, tuned to your role and level."),
        ("📈", "Adaptive Interviews", "Difficulty rises or eases based on how you're actually performing."),
        ("🎙️", "Voice Answers", "Speak your answers; transcription is editable before you submit."),
        ("⚡", "Real-Time Evaluation", "Every answer is scored across 7 rubric dimensions as you go."),
        ("📊", "Interview Analytics", "See your score trend, strengths, and weak spots question by question."),
        ("📄", "Downloadable Reports", "A recruiter-style PDF report you can keep and share."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""<div class="feature-card">
                        <div style="font-size:28px;">{icon}</div>
                        <div style="font-weight:600; color:#f8fafc; margin-top:8px;">{title}</div>
                        <div style="font-size:14px; margin-top:6px;">{desc}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
        if i % 3 == 2:
            st.markdown("<br>", unsafe_allow_html=True)


def _history_report() -> None:
    interview_id = st.session_state.get("selected_interview_id")
    interview = get_interview_full(interview_id) if interview_id else None
    if not interview:
        st.error("Interview not found.")
        return
    st.markdown(f"## {interview.target_role} — {interview.interview_type} Interview")
    st.caption(interview.completed_at.strftime("%B %d, %Y"))
    st.markdown(f"### Overall Score: **{interview.overall_score:.0f}/100** — {interview.readiness}")
    cols = st.columns(3)
    cats = [
        ("Technical", interview.technical_score), ("Communication", interview.communication_score),
        ("Problem Solving", interview.problem_solving_score), ("Confidence", interview.confidence_score),
        ("Relevance", interview.relevance_score), ("Structure", interview.structure_score),
    ]
    for i, (label, val) in enumerate(cats):
        cols[i % 3].metric(label, f"{val:.0f}%")
    st.info(interview.final_verdict or "")

    pdf_bytes = build_report_pdf(interview, candidate_name="Candidate")
    st.download_button(
        "📄 Download PDF Report", data=pdf_bytes,
        file_name=f"interview_os_report_{interview.id[:8]}.pdf", mime="application/pdf",
    )
    if st.button("Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


def main() -> None:
    _sidebar()
    page = st.session_state.page

    if page == "landing":
        _landing()
    elif page == "setup":
        setup.render(st.session_state.user_id)
    elif page == "interview":
        if st.session_state.interview_state is None:
            st.session_state.page = "setup"
            st.rerun()
        interview_ui.render(st.session_state.user_id)
    elif page == "results":
        results.render(st.session_state.user_id)
    elif page == "dashboard":
        dashboard.render(st.session_state.user_id)
    elif page == "history_report":
        _history_report()
    else:
        st.session_state.page = "landing"
        st.rerun()


if __name__ == "__main__":
    main()
