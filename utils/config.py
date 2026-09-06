"""
Central configuration module.

All environment variables are read exactly once, here. No other module
should call os.environ / os.getenv directly — this keeps secrets out of
business logic and makes it obvious where config comes from.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./interview_os.db")

    app_env: str = os.getenv("APP_ENV", "development")
    session_secret: str = os.getenv("SESSION_SECRET", "dev-secret-change-me")

    speech_to_text_provider: str | None = os.getenv("SPEECH_TO_TEXT_PROVIDER") or None

    @property
    def llm_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def voice_enabled(self) -> bool:
        return bool(self.speech_to_text_provider)


settings = Settings()