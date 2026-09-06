"""Engine/session management + small repository helpers.

Streamlit reruns the whole script on every interaction, so we keep one
process-wide engine (cheap to create) and open a fresh session per call
rather than holding a long-lived session across reruns.
"""
from __future__ import annotations

import json
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Interview, InterviewQuestion, Answer, Evaluation, User
from utils.config import settings
from utils.helpers import new_id

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------- repos ----

def get_or_create_user(name: str = "Candidate", user_id: str | None = None) -> str:
    with get_session() as db:
        if user_id:
            existing = db.get(User, user_id)
            if existing:
                return existing.id
        user = User(id=new_id(), name=name)
        db.add(user)
        db.flush()
        return user.id


def create_interview(user_id: str, config: dict) -> str:
    with get_session() as db:
        interview = Interview(
            id=new_id(),
            user_id=user_id,
            target_role=config["target_role"],
            experience_level=config["experience_level"],
            interview_type=config["interview_type"],
            difficulty_start=config["difficulty"],
            num_questions=config["num_questions"],
        )
        db.add(interview)
        db.flush()
        return interview.id


def add_question(interview_id: str, sequence: int, topic: str, difficulty: str, text: str) -> str:
    with get_session() as db:
        q = InterviewQuestion(
            id=new_id(),
            interview_id=interview_id,
            sequence=sequence,
            topic=topic,
            difficulty=difficulty,
            question_text=text,
        )
        db.add(q)
        db.flush()
        return q.id


def set_response_time(question_id: str, seconds: float) -> None:
    with get_session() as db:
        q = db.get(InterviewQuestion, question_id)
        if q:
            q.response_time_seconds = seconds


def add_answer_with_evaluation(question_id: str, answer_text: str, input_mode: str, eval_result: dict) -> None:
    with get_session() as db:
        answer = Answer(id=new_id(), question_id=question_id, answer_text=answer_text, input_mode=input_mode)
        db.add(answer)
        db.flush()

        evaluation = Evaluation(
            id=new_id(),
            answer_id=answer.id,
            technical_accuracy=eval_result["technical_accuracy"],
            relevance=eval_result["relevance"],
            completeness=eval_result["completeness"],
            communication=eval_result["communication"],
            confidence=eval_result["confidence"],
            problem_solving=eval_result["problem_solving"],
            answer_structure=eval_result["answer_structure"],
            overall=eval_result["overall"],
            strengths_json=json.dumps(eval_result.get("strengths", [])),
            weaknesses_json=json.dumps(eval_result.get("weaknesses", [])),
            interviewer_notes=eval_result.get("interviewer_notes", ""),
        )
        db.add(evaluation)


def finalize_interview(interview_id: str, summary: dict) -> None:
    with get_session() as db:
        interview = db.get(Interview, interview_id)
        if not interview:
            return
        interview.status = "complete"
        interview.overall_score = summary["overall_score"]
        interview.technical_score = summary["technical_score"]
        interview.communication_score = summary["communication_score"]
        interview.problem_solving_score = summary["problem_solving_score"]
        interview.confidence_score = summary["confidence_score"]
        interview.relevance_score = summary["relevance_score"]
        interview.structure_score = summary["structure_score"]
        interview.readiness = summary["readiness"]
        interview.final_verdict = summary["final_verdict"]
        interview.improvement_plan_json = json.dumps(summary["improvement_plan"])
        interview.total_duration_seconds = summary.get("total_duration_seconds")
        from datetime import datetime
        interview.completed_at = datetime.utcnow()


def get_interview_full(interview_id: str) -> Interview | None:
    with get_session() as db:
        interview = db.get(Interview, interview_id)
        if interview:
            _ = [ (q, q.answer, q.answer.evaluation if q.answer else None) for q in interview.questions ]
        return interview


def list_user_interviews(user_id: str) -> list[Interview]:
    with get_session() as db:
        user = db.get(User, user_id)
        if not user:
            return []
        return list(user.interviews)
