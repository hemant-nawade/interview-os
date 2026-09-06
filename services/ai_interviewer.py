"""
Single point of contact with the LLM.

Every other service (question_engine, evaluator, report_generator) calls
through here instead of importing the provider SDK directly. That keeps
prompt/response plumbing and error handling in one place, and means
swapping providers later touches only this file.
"""
from __future__ import annotations

import logging

from utils.config import settings

logger = logging.getLogger("interview_os.ai")

_client = None


class AIUnavailableError(RuntimeError):
    """Raised when no LLM API key is configured or the call fails."""


def _get_client():
    global _client
    if _client is None:
        if not settings.llm_enabled:
            raise AIUnavailableError(
                "No GROQ_API_KEY configured. Set it in your .env to enable "
                "live interviews; see .env.example."
            )
        from groq import Groq
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def ask_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
    """Send one prompt, return raw text."""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=settings.groq_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        logger.debug("LLM call ok, %d chars returned", len(text))
        return text
    except AIUnavailableError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("LLM call failed: %s", exc)
        raise AIUnavailableError(f"The AI interviewer is temporarily unavailable ({type(exc).__name__}: {exc}).") from exc