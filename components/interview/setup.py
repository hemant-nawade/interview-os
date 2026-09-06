"""Interview setup / configuration screen."""
from __future__ import annotations

import streamlit as st

from database.database import create_interview

ROLE_PRESETS = [
    "Python Developer",
    "Full Stack Developer",
    "Data Analyst",
    "Software Engineer",
    "Java Developer",
    "Frontend Developer",
    "Backend Developer",
    "Custom role...",
]


def render(user_id: str) -> None:
    st.subheader("Configure Your Interview")

    with st.form("interview_setup"):
        col1, col2 = st.columns(2)
        with col1:
            role_choice = st.selectbox("Target Role", ROLE_PRESETS)
            target_role = role_choice
            if role_choice == "Custom role...":
                target_role = st.text_input("Enter custom role", placeholder="e.g. DevOps Engineer")

            experience_level = st.selectbox(
                "Experience Level", ["Student", "Fresher", "1-2 Years", "3-5 Years"]
            )
        with col2:
            interview_type = st.selectbox(
                "Interview Type", ["Technical", "HR", "Behavioral", "Coding", "Mixed"]
            )
            difficulty = st.select_slider("Starting Difficulty", ["Easy", "Medium", "Hard"], value="Medium")

        num_questions = st.radio("Number of Questions", [5, 10, 15], horizontal=True, index=0)

        submitted = st.form_submit_button("START INTERVIEW", use_container_width=True, type="primary")

    if submitted:
        if not target_role or role_choice == "Custom role..." and not target_role.strip():
            st.error("Please enter a target role.")
            return

        config = {
            "target_role": target_role,
            "experience_level": experience_level,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "num_questions": num_questions,
        }
        interview_id = create_interview(user_id, config)

        st.session_state.page = "interview"
        st.session_state.interview_state = {
            **config,
            "interview_id": interview_id,
            "current_difficulty": difficulty,
            "history": [],
            "current_question": None,
            "current_question_id": None,
            "question_started_at": None,
            "total_duration_seconds": 0.0,
            "interview_started_at": None,
        }
        st.rerun()
