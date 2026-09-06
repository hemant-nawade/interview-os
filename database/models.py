"""
Database models for Interview OS.

Works against SQLite out of the box (DATABASE_URL default) and against
PostgreSQL / Supabase unchanged when DATABASE_URL is swapped in .env —
this is plain SQLAlchemy, no SQLite-only types are used.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, default="Candidate")
    email = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    target_role = Column(String, nullable=False)
    experience_level = Column(String, nullable=False)
    interview_type = Column(String, nullable=False)
    difficulty_start = Column(String, nullable=False)
    num_questions = Column(Integer, nullable=False)

    status = Column(String, default="in_progress")  # in_progress | complete
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    problem_solving_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    structure_score = Column(Float, nullable=True)

    readiness = Column(String, nullable=True)
    final_verdict = Column(Text, nullable=True)
    improvement_plan_json = Column(Text, nullable=True)  # JSON blob

    total_duration_seconds = Column(Float, nullable=True)

    user = relationship("User", back_populates="interviews")
    questions = relationship(
        "InterviewQuestion", back_populates="interview", cascade="all, delete-orphan",
        order_by="InterviewQuestion.sequence",
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(String, primary_key=True)
    interview_id = Column(String, ForeignKey("interviews.id"), nullable=False)

    sequence = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    asked_at = Column(DateTime, default=datetime.utcnow)
    response_time_seconds = Column(Float, nullable=True)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship(
        "Answer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("interview_questions.id"), nullable=False)

    answer_text = Column(Text, nullable=False)
    input_mode = Column(String, default="text")  # text | voice
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("InterviewQuestion", back_populates="answer")
    evaluation = relationship(
        "Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan"
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True)
    answer_id = Column(String, ForeignKey("answers.id"), nullable=False)

    technical_accuracy = Column(Float, nullable=False)
    relevance = Column(Float, nullable=False)
    completeness = Column(Float, nullable=False)
    communication = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    problem_solving = Column(Float, nullable=False)
    answer_structure = Column(Float, nullable=False)
    overall = Column(Float, nullable=False)

    strengths_json = Column(Text, nullable=True)   # JSON list
    weaknesses_json = Column(Text, nullable=True)  # JSON list
    interviewer_notes = Column(Text, nullable=True)

    answer = relationship("Answer", back_populates="evaluation")
