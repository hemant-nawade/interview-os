"""Candidate dashboard: stats + interview history ('My Interviews')."""
from __future__ import annotations

import streamlit as st

from database.database import list_user_interviews


def render(user_id: str) -> None:
    interviews = [i for i in list_user_interviews(user_id) if i.status == "complete"]

    st.subheader("Your Dashboard")

    if not interviews:
        st.info("No completed interviews yet. Start one to see your stats here.")
        if st.button("Start Interview", type="primary"):
            st.session_state.page = "setup"
            st.rerun()
        return

    scores = [i.overall_score for i in interviews]
    avg_score = sum(scores) / len(scores)
    best_score = max(scores)

    category_map = {
        "Technical Skills": [i.technical_score for i in interviews],
        "Communication": [i.communication_score for i in interviews],
        "Problem Solving": [i.problem_solving_score for i in interviews],
        "Confidence": [i.confidence_score for i in interviews],
        "Relevance": [i.relevance_score for i in interviews],
        "Answer Structure": [i.structure_score for i in interviews],
    }
    avg_by_category = {k: sum(v) / len(v) for k, v in category_map.items()}
    strongest = max(avg_by_category, key=avg_by_category.get)
    weakest = min(avg_by_category, key=avg_by_category.get)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Interviews", len(interviews))
    c2.metric("Average Score", f"{avg_score:.0f}")
    c3.metric("Best Score", f"{best_score:.0f}")
    c4.metric("Readiness", interviews[-1].readiness or "-")

    c5, c6 = st.columns(2)
    c5.metric("Strongest Skill", strongest)
    c6.metric("Weakest Skill", weakest)

    st.divider()
    st.markdown("### My Interviews")
    for interview in sorted(interviews, key=lambda i: i.completed_at, reverse=True):
        with st.container(border=True):
            cols = st.columns([3, 2, 2, 2])
            cols[0].markdown(f"**{interview.target_role}**  \n{interview.interview_type} Interview")
            cols[1].markdown(f"**{interview.overall_score:.0f}/100**")
            cols[2].markdown(interview.completed_at.strftime("%B %d, %Y"))
            if cols[3].button("View Report", key=f"view_{interview.id}"):
                st.session_state.page = "history_report"
                st.session_state.selected_interview_id = interview.id
                st.rerun()

    st.divider()
    st.caption(
        f"Recommended practice: focus on **{weakest}** — try another "
        f"{interviews[-1].interview_type} interview at the same or next difficulty."
    )
