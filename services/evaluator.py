"""
Answer evaluation.

Scores a single answer 0-100 across the seven rubric dimensions the spec
calls for, plus strengths/weaknesses/interviewer notes. This is the only
place scoring happens, so the adaptive-difficulty logic and the final
report both read from the same rubric.
"""
from __future__ import annotations

from utils.helpers import clamp, safe_json_loads
from services.ai_interviewer import ask_llm

SYSTEM_PROMPT = """You are grading a candidate's spoken/written interview \
answer as a strict but fair technical interviewer. Score honestly — do not \
default to high scores. Respond ONLY with valid JSON, no prose."""

DIMENSIONS = [
    "technical_accuracy",
    "relevance",
    "completeness",
    "communication",
    "confidence",
    "problem_solving",
    "answer_structure",
]


def evaluate_answer(
    question: str,
    answer: str,
    target_role: str,
    topic: str,
    difficulty: str,
) -> dict:
    if not answer or not answer.strip():
        return {
            **{d: 0 for d in DIMENSIONS},
            "overall": 0,
            "strengths": [],
            "weaknesses": ["No answer was provided."],
            "interviewer_notes": "Candidate did not answer this question.",
        }

    prompt = f"""
Role: {target_role}
Topic: {topic}
Difficulty: {difficulty}
Question: {question}
Candidate answer: {answer}

Score the answer 0-100 on each of: technical_accuracy, relevance,
completeness, communication, confidence, problem_solving, answer_structure.
Then list 2-4 short strengths, 2-4 short weaknesses, and one short internal
interviewer note (1-2 sentences, not shown to the candidate during the
interview).

Return JSON exactly like:
{{
  "technical_accuracy": 0-100, "relevance": 0-100, "completeness": 0-100,
  "communication": 0-100, "confidence": 0-100, "problem_solving": 0-100,
  "answer_structure": 0-100,
  "strengths": ["..."], "weaknesses": ["..."], "interviewer_notes": "..."
}}
"""
    raw = ask_llm(SYSTEM_PROMPT, prompt)
    data = safe_json_loads(raw, default={})

    scores = {d: clamp(float(data.get(d, 50))) for d in DIMENSIONS}
    overall = clamp(sum(scores.values()) / len(scores))

    return {
        **scores,
        "overall": overall,
        "strengths": data.get("strengths", []),
        "weaknesses": data.get("weaknesses", []),
        "interviewer_notes": data.get("interviewer_notes", ""),
    }
