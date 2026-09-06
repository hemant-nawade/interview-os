"""
Central configuration module.

All environment variables are read exactly once, here. No other module
should call os.environ / os.getenv directly — this keeps secrets out of
business logic and makes it obvious where config comes from.

Works both locally (.env file via python-dotenv) and on Streamlit
Community Cloud (values set in the app's "Secrets" panel, exposed via
st.secrets rather than the OS environment).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_setting(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value:
        return value
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None = _get_setting("GROQ_API_KEY")
    groq_model: str = _get_setting("GROQ_MODEL", "openai/gpt-oss-20b")

    database_url: str = _get_setting("DATABASE_URL", "sqlite:///./interview_os.db")

    app_env: str = _get_setting("APP_ENV", "development")
    session_secret: str = _get_setting("SESSION_SECRET", "dev-secret-change-me")

    speech_to_text_provider: str | None = _get_setting("SPEECH_TO_TEXT_PROVIDER") or None

    @property
    def llm_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def voice_enabled(self) -> bool:
        return bool(self.speech_to_text_provider)


settings = Settings()