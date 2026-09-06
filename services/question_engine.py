"""
Question generation.

Deliberately does NOT pre-generate a question list. Each call looks at
everything that happened so far (role, type, difficulty, last answer +
score + topic) and asks the LLM for exactly one next question — this is
what makes the interview adaptive rather than a fixed quiz.
"""
from __future__ import annotations

from utils.helpers import safe_json_loads
from services.ai_interviewer import ask_llm

SYSTEM_PROMPT = """You are an experienced technical/HR interviewer conducting a \
realistic mock interview. You are professional, calm, respectful, and \
slightly challenging — never insulting, never overly enthusiastic. You give \
minimal feedback during the interview itself (a short acknowledgement, not a \
score). Respond ONLY with valid JSON, no prose, no markdown fences."""


def _history_block(history: list[dict]) -> str:
    if not history:
        return "This is the first question of the interview."
    lines = []
    for h in history:
        lines.append(
            f"- Q(topic={h['topic']}, difficulty={h['difficulty']}): {h['question']}\n"
            f"  Candidate answer: {h['answer'][:400]}\n"
            f"  Score: {h['score']}/100"
        )
    return "Interview so far:\n" + "\n".join(lines)


def generate_next_question(
    target_role: str,
    interview_type: str,
    experience_level: str,
    difficulty: str,
    history: list[dict],
    question_number: int,
    total_questions: int,
) -> dict:
    """Returns {"topic": str, "question": str, "transition_remark": str}."""
    prompt = f"""
Role: {target_role}
Experience level: {experience_level}
Interview type: {interview_type}
Current difficulty: {difficulty}
This is question {question_number} of {total_questions}.

{_history_block(history)}

Generate the NEXT interview question. If there is a previous answer, first
decide a brief in-character transition remark (one sentence, e.g. "Good
explanation, let's go one level deeper." or "That's okay, let's approach
this from a simpler angle.") that fits the score, then ask a question that
fits the current difficulty and naturally follows from the candidate's
performance and the interview type. Do not repeat a topic already covered
unless going deeper. On the last question, you may ask a wrap-up or
reflective question appropriate to the interview type.

Return JSON exactly like:
{{"transition_remark": "...", "topic": "short topic name", "question": "the interview question text"}}
"""
    raw = ask_llm(SYSTEM_PROMPT, prompt)
    data = safe_json_loads(raw, default={})
    return {
        "transition_remark": data.get("transition_remark", ""),
        "topic": data.get("topic", target_role),
        "question": data.get("question") or "Tell me about a project you're proud of and why.",
    }
