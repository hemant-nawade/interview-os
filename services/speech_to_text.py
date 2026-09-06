"""
Speech-to-text.

Kept behind `settings.voice_enabled` so the MVP ships with a clean text-only
flow (spec stage 12+ adds voice). The interface is intentionally provider-
agnostic: swap the body of `transcribe()` for Whisper API / any STT vendor
without touching interview_ui.py, which only calls this function.
"""
from __future__ import annotations

from utils.config import settings


class TranscriptionError(RuntimeError):
    pass


def transcribe(audio_bytes: bytes) -> str:
    if not settings.voice_enabled:
        raise TranscriptionError(
            "Voice mode is not configured yet. Set SPEECH_TO_TEXT_PROVIDER in "
            ".env to enable it (see README roadmap)."
        )
    # Placeholder for the real provider call (e.g. Whisper API). Left as a
    # single, obvious integration point for the next stage:
    #
    #   import openai
    #   result = openai.audio.transcriptions.create(file=..., model="whisper-1")
    #   return result.text
    raise NotImplementedError("Wire up your chosen STT provider here.")
