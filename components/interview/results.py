"""Interview completion / results / analytics screen."""
from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database.database import get_interview_full
from services.report_generator import build_report_pdf
from utils.helpers import format_duration


def render(user_id: str) -> None:
    state = st.session_state.interview_state
    summary = state["summary"]

    st.balloons()
    st.markdown("## 🎉 INTERVIEW COMPLETE")
    st.markdown(f"### Overall Score: **{summary['overall_score']:.0f} / 100** — {summary['readiness']}")

    categories = {
        "Technical Skills": summary["technical_score"],
        "Communication": summary["communication_score"],
        "Problem Solving": summary["problem_solving_score"],
        "Confidence": summary["confidence_score"],
        "Relevance": summary["relevance_score"],
        "Answer Structure": summary["structure_score"],
    }
    cols = st.columns(3)
    for i, (label, val) in enumerate(categories.items()):
        cols[i % 3].metric(label, f"{val:.0f}%")

    st.markdown("#### AI Final Verdict")
    st.info(summary["final_verdict"])

    plan = summary["improvement_plan"]
    if plan:
        st.markdown("#### Personalized Improvement Plan")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Top Strengths**")
            for s in plan.get("top_strengths", []):
                st.markdown(f"- {s}")
            st.markdown("**Topics To Study**")
            for s in plan.get("topics_to_study", []):
                st.markdown(f"- {s}")
            st.markdown("**Recommended Projects**")
            for s in plan.get("recommended_projects", []):
                st.markdown(f"- {s}")
        with c2:
            st.markdown("**Top Weaknesses**")
            for s in plan.get("top_weaknesses", []):
                st.markdown(f"- {s}")
            st.markdown("**Interview Tips**")
            for s in plan.get("interview_tips", []):
                st.markdown(f"- {s}")
        if plan.get("next_interview_recommendation"):
            st.success(f"**Next up:** {plan['next_interview_recommendation']}")

    st.markdown("#### Performance Trend")
    trend_df = pd.DataFrame(
        {
            "Question": [f"Q{i+1}" for i in range(len(state["history"]))],
            "Score": [h["evaluation"]["overall"] for h in state["history"]],
        }
    )
    fig = go.Figure(go.Scatter(x=trend_df["Question"], y=trend_df["Score"], mode="lines+markers", line=dict(color="#6366f1", width=3)))
    fig.update_layout(
        template="plotly_dark", height=320, margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)

    if state.get("total_duration_seconds"):
        st.caption(f"Total interview duration: {format_duration(state['total_duration_seconds'])}")

    st.divider()
    interview = get_interview_full(state["interview_id"])
    pdf_bytes = build_report_pdf(interview, candidate_name="Candidate")
    st.download_button(
        "📄 Download PDF Report", data=pdf_bytes,
        file_name=f"interview_os_report_{state['interview_id'][:8]}.pdf",
        mime="application/pdf", type="primary", use_container_width=True,
    )

    col_a, col_b = st.columns(2)
    if col_a.button("Start Another Interview", use_container_width=True):
        st.session_state.page = "setup"
        st.session_state.interview_state = None
        st.rerun()
    if col_b.button("Go to Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()
