"""
AIInterviewerAvatar — isolated presentation component.

This is the ONLY place that knows how the interviewer is rendered. The
interview engine and UI only ever set a `speaking_state` and pass
`current_text`; when a talking-avatar / TTS / lip-sync pipeline is added
later, only this file changes:

    LLM response -> Text-to-Speech -> Avatar speaking animation -> candidate

State machine: IDLE -> THINKING -> SPEAKING -> LISTENING -> IDLE ...
"""
from __future__ import annotations

import streamlit as st

STATES = ("IDLE", "THINKING", "SPEAKING", "LISTENING")

_STATE_COPY = {
    "IDLE": ("●", "#64748b", "Ready"),
    "THINKING": ("◐", "#f59e0b", "Thinking..."),
    "SPEAKING": ("◉", "#6366f1", "Speaking"),
    "LISTENING": ("◎", "#22c55e", "Listening..."),
}


def render(
    interviewer_name: str = "Ava",
    avatar_image: str | None = None,
    speaking_state: str = "IDLE",
    current_text: str = "",
) -> None:
    """Render the interviewer panel. `avatar_image` is an optional path/URL
    for a static portrait — future stages can pass a video/canvas element
    here instead without changing the call site."""
    if speaking_state not in STATES:
        speaking_state = "IDLE"
    icon, color, label = _STATE_COPY[speaking_state]

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(160deg, #111827 0%, #1e1b4b 100%);
            border-radius: 20px; padding: 28px; text-align: center;
            border: 1px solid #312e81;">
            <div style="
                width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 16px;
                background: radial-gradient(circle at 35% 30%, #4f46e5, #1e1b4b);
                display: flex; align-items: center; justify-content: center;
                font-size: 42px; color: white; border: 3px solid {color};">
                🤖
            </div>
            <div style="color:#f8fafc; font-size:18px; font-weight:600;">{interviewer_name}</div>
            <div style="color:{color}; font-size:13px; margin-top:4px;">{icon} {label}</div>
            <div style="color:#cbd5e1; font-size:14px; margin-top:18px; min-height: 60px;">
                {current_text or ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
