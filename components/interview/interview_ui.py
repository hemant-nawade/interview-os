"""Live interview screen: asks questions, takes answers, scores them, and
adapts difficulty for the next question."""
from __future__ import annotations

import time

import streamlit as st

from components.avatar import AIInterviewerAvatar
from database.database import (
    add_answer_with_evaluation,
    add_question,
    finalize_interview,
    set_response_time,
)
from services import interview_engine
from services.ai_interviewer import AIUnavailableError
from services.speech_to_text import TranscriptionError, transcribe
from utils.config import settings
from utils.helpers import format_duration


def _ensure_current_question(state: dict) -> None:
    if state["current_question"] is not None:
        return
    with st.spinner("Interviewer is preparing the next question..."):
        try:
            q = interview_engine.get_next_question(state)
        except AIUnavailableError as exc:
            st.error(str(exc))
            st.stop()
    state["current_question"] = q
    state["current_question_id"] = add_question(
        state["interview_id"], len(state["history"]) + 1, q["topic"], state["current_difficulty"], q["question"]
    )
    state["question_started_at"] = time.time()
    if state["interview_started_at"] is None:
        state["interview_started_at"] = state["question_started_at"]


def render(user_id: str) -> None:
    state = st.session_state.interview_state
    _ensure_current_question(state)

    total = state["num_questions"]
    current_num = len(state["history"]) + 1
    q = state["current_question"]

    left, right = st.columns([1, 1.4])

    with left:
        AIInterviewerAvatar.render(
            interviewer_name="Ava",
            speaking_state="SPEAKING",
            current_text=(q["transition_remark"] + " " + q["question"]).strip(),
        )

    with right:
        st.progress(current_num / total, text=f"Question {current_num} / {total}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Topic", q["topic"])
        m2.metric("Difficulty", state["current_difficulty"])
        elapsed = time.time() - state["interview_started_at"] if state["interview_started_at"] else 0
        m3.metric("Elapsed", format_duration(elapsed))

        st.markdown("#### Your Answer")
        mode = st.radio("Input mode", ["Text", "Voice"], horizontal=True, label_visibility="collapsed")

        answer_text = ""
        if mode == "Text":
            answer_text = st.text_area("Type your answer", height=160, key=f"answer_{current_num}")
        else:
            if not settings.voice_enabled:
                st.info("Voice mode isn't configured yet — switch to Text for now (see README roadmap).")
            audio = st.audio_input("🎙️ Answer with Voice") if settings.voice_enabled else None
            if audio is not None:
                try:
                    transcript = transcribe(audio.getvalue())
                    answer_text = st.text_area(
                        "Transcribed Answer (edit if needed)", value=transcript, height=160
                    )
                except TranscriptionError as exc:
                    st.warning(str(exc))

        if st.button("Submit Answer", type="primary", use_container_width=True):
            _submit_answer(state, q, answer_text)


def _submit_answer(state: dict, q: dict, answer_text: str) -> None:
    response_time = time.time() - state["question_started_at"]
    set_response_time(state["current_question_id"], response_time)

    with st.spinner("Evaluating your answer..."):
        try:
            evaluation = interview_engine.score_answer(q["question"], answer_text, state, q["topic"])
        except AIUnavailableError as exc:
            st.error(str(exc))
            return

    add_answer_with_evaluation(state["current_question_id"], answer_text, "text", evaluation)

    state["history"].append(
        {
            "topic": q["topic"],
            "difficulty": state["current_difficulty"],
            "question": q["question"],
            "answer": answer_text,
            "evaluation": evaluation,
            "score": evaluation["overall"],
            "response_time_seconds": response_time,
        }
    )
    interview_engine.update_difficulty(state, evaluation["overall"])
    state["current_question"] = None
    state["current_question_id"] = None

    if len(state["history"]) >= state["num_questions"]:
        state["total_duration_seconds"] = time.time() - state["interview_started_at"]
        summary = interview_engine.build_summary(state)
        finalize_interview(state["interview_id"], summary)
        state["summary"] = summary
        st.session_state.page = "results"

    st.rerun()
