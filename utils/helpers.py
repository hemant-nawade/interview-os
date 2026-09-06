"""Small shared utilities. No business logic lives here — just formatting
and defensive helpers used by multiple layers."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def safe_json_loads(text: str, default=None):
    """LLMs occasionally wrap JSON in prose or code fences. Extract the
    first {...} or [...] block before parsing so a stray sentence doesn't
    crash the whole evaluation step."""
    if default is None:
        default = {}
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return default


def readiness_label(score: float) -> str:
    if score < 45:
        return "Not Ready"
    if score < 65:
        return "Needs Practice"
    if score < 82:
        return "Almost Ready"
    return "Interview Ready"


def next_difficulty(current: str, score: float) -> str:
    """Core adaptive-difficulty rule from the spec, isolated so the
    interview engine and any future tuning can reuse/override it."""
    levels = ["Easy", "Medium", "Hard"]
    idx = levels.index(current) if current in levels else 1

    if score > 85:
        idx = min(idx + 1, len(levels) - 1)
    elif score >= 70:
        pass  # maintain
    elif score >= 50:
        idx = max(idx - 0, 0)  # related question, same-ish difficulty
    else:
        idx = max(idx - 1, 0)  # reduce difficulty, test fundamentals

    return levels[idx]
