"""
Interview orchestration.

Ties question_engine + evaluator + the adaptive-difficulty rule together,
and produces the end-of-interview summary (category scores, verdict,
improvement plan). Streamlit UI code should only ever call into this
module — it should never call question_engine/evaluator directly, so the
adaptive logic stays in one testable place.
"""
from __future__ import annotations

from utils.helpers import clamp, next_difficulty, readiness_label, safe_json_loads
from services import question_engine, evaluator
from services.ai_interviewer import ask_llm

CATEGORY_KEYS = [
    "technical_score",
    "communication_score",
    "problem_solving_score",
    "confidence_score",
    "relevance_score",
    "structure_score",
]

_DIM_TO_CATEGORY = {
    "technical_accuracy": "technical_score",
    "communication": "communication_score",
    "problem_solving": "problem_solving_score",
    "confidence": "confidence_score",
    "relevance": "relevance_score",
    "answer_structure": "structure_score",
}


def get_next_question(state: dict) -> dict:
    """state holds the in-progress interview's config + running history
    (see components/interview/interview_ui.py for the shape)."""
    return question_engine.generate_next_question(
        target_role=state["target_role"],
        interview_type=state["interview_type"],
        experience_level=state["experience_level"],
        difficulty=state["current_difficulty"],
        history=state["history"],
        question_number=len(state["history"]) + 1,
        total_questions=state["num_questions"],
    )


def score_answer(question: str, answer: str, state: dict, topic: str) -> dict:
    result = evaluator.evaluate_answer(
        question=question,
        answer=answer,
        target_role=state["target_role"],
        topic=topic,
        difficulty=state["current_difficulty"],
    )
    return result


def update_difficulty(state: dict, score: float) -> str:
    new_difficulty = next_difficulty(state["current_difficulty"], score)
    state["current_difficulty"] = new_difficulty
    return new_difficulty


def build_summary(state: dict) -> dict:
    """Aggregate all per-question evaluations into the final report data."""
    history = state["history"]
    if not history:
        raise ValueError("Cannot summarize an interview with no answered questions.")

    category_totals = {k: [] for k in CATEGORY_KEYS}
    for h in history:
        ev = h["evaluation"]
        for dim, cat in _DIM_TO_CATEGORY.items():
            category_totals[cat].append(ev[dim])

    category_avgs = {k: clamp(sum(v) / len(v)) for k, v in category_totals.items()}
    overall_score = clamp(sum(h["evaluation"]["overall"] for h in history) / len(history))
    readiness = readiness_label(overall_score)

    verdict_and_plan = _generate_verdict_and_plan(state, category_avgs, overall_score, readiness)

    return {
        "overall_score": overall_score,
        **category_avgs,
        "readiness": readiness,
        "final_verdict": verdict_and_plan["final_verdict"],
        "improvement_plan": verdict_and_plan["improvement_plan"],
        "total_duration_seconds": state.get("total_duration_seconds"),
    }


def _generate_verdict_and_plan(state: dict, category_avgs: dict, overall_score: float, readiness: str) -> dict:
    history = state["history"]
    topics = ", ".join(sorted({h["topic"] for h in history}))
    weak_points = []
    for h in history:
        weak_points.extend(h["evaluation"].get("weaknesses", []))

    prompt = f"""
Role: {state['target_role']}
Experience level: {state['experience_level']}
Interview type: {state['interview_type']}
Topics covered: {topics}
Overall score: {overall_score:.0f}/100
Category scores: {category_avgs}
Readiness bucket: {readiness}
Observed weaknesses across the interview: {weak_points[:15]}

Write a short (3-4 sentence) recruiter-style final verdict paragraph, then a
personalized improvement plan.

Return JSON exactly like:
{{
  "final_verdict": "...",
  "improvement_plan": {{
    "top_strengths": ["...", "...", "..."],
    "top_weaknesses": ["...", "...", "..."],
    "topics_to_study": ["...", "..."],
    "recommended_projects": ["...", "..."],
    "interview_tips": ["...", "..."],
    "next_interview_recommendation": "one sentence"
  }}
}}
"""
    raw = ask_llm(question_engine.SYSTEM_PROMPT, prompt, max_tokens=900)
    data = safe_json_loads(raw, default={})
    return {
        "final_verdict": data.get(
            "final_verdict",
            "The candidate completed the interview; a detailed AI verdict could not be generated this time.",
        ),
        "improvement_plan": data.get("improvement_plan", {}),
    }
