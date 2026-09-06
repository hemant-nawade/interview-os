"""Generates the downloadable PDF performance report."""
from __future__ import annotations

import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DARK = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#6366f1")
MUTED = colors.HexColor("#64748b")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TitleBig", parent=styles["Title"], textColor=DARK, fontSize=22))
    styles.add(ParagraphStyle("H2", parent=styles["Heading2"], textColor=ACCENT, spaceBefore=14))
    styles.add(ParagraphStyle("Body", parent=styles["BodyText"], leading=15))
    styles.add(ParagraphStyle("Muted", parent=styles["BodyText"], textColor=MUTED))
    return styles


def build_report_pdf(interview, candidate_name: str) -> bytes:
    """interview is a database.models.Interview loaded with .questions[].answer.evaluation"""
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story = []

    story.append(Paragraph("INTERVIEW OS", styles["TitleBig"]))
    story.append(Paragraph("AI Interview Performance Report", styles["Muted"]))
    story.append(Spacer(1, 12))

    meta_rows = [
        ["Candidate", candidate_name],
        ["Target Role", interview.target_role],
        ["Experience Level", interview.experience_level],
        ["Interview Type", interview.interview_type],
        ["Date", (interview.completed_at or datetime.utcnow()).strftime("%B %d, %Y")],
        ["Overall Score", f"{interview.overall_score:.0f} / 100"],
        ["Interview Readiness", interview.readiness or "-"],
    ]
    meta_table = Table(meta_rows, colWidths=[5 * cm, 10 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
            ]
        )
    )
    story.append(meta_table)

    story.append(Paragraph("Category Scores", styles["H2"]))
    cat_rows = [
        ["Technical Skills", f"{interview.technical_score:.0f}%"],
        ["Communication", f"{interview.communication_score:.0f}%"],
        ["Problem Solving", f"{interview.problem_solving_score:.0f}%"],
        ["Confidence", f"{interview.confidence_score:.0f}%"],
        ["Relevance", f"{interview.relevance_score:.0f}%"],
        ["Answer Structure", f"{interview.structure_score:.0f}%"],
    ]
    cat_table = Table(cat_rows, colWidths=[7 * cm, 3 * cm])
    cat_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ]
        )
    )
    story.append(cat_table)

    story.append(Paragraph("Question-by-Question Evaluation", styles["H2"]))
    for q in interview.questions:
        story.append(Paragraph(f"<b>Q{q.sequence}. ({q.topic}, {q.difficulty})</b> {q.question_text}", styles["Body"]))
        if q.answer:
            story.append(Paragraph(f"<i>Answer:</i> {q.answer.answer_text[:600]}", styles["Body"]))
            if q.answer.evaluation:
                ev = q.answer.evaluation
                story.append(Paragraph(f"Score: {ev.overall:.0f}/100", styles["Muted"]))
                strengths = json.loads(ev.strengths_json or "[]")
                weaknesses = json.loads(ev.weaknesses_json or "[]")
                if strengths:
                    story.append(Paragraph("Strengths: " + "; ".join(strengths), styles["Muted"]))
                if weaknesses:
                    story.append(Paragraph("Weaknesses: " + "; ".join(weaknesses), styles["Muted"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("AI Final Verdict", styles["H2"]))
    story.append(Paragraph(interview.final_verdict or "-", styles["Body"]))

    plan = json.loads(interview.improvement_plan_json or "{}")
    if plan:
        story.append(Paragraph("Personalized Improvement Plan", styles["H2"]))
        for label, key in [
            ("Top Strengths", "top_strengths"),
            ("Top Weaknesses", "top_weaknesses"),
            ("Topics To Study", "topics_to_study"),
            ("Recommended Projects", "recommended_projects"),
            ("Interview Tips", "interview_tips"),
        ]:
            items = plan.get(key) or []
            if items:
                story.append(Paragraph(f"<b>{label}:</b> " + "; ".join(items), styles["Body"]))
        if plan.get("next_interview_recommendation"):
            story.append(Paragraph(f"<b>Next Step:</b> {plan['next_interview_recommendation']}", styles["Body"]))

    doc.build(story)
    return buf.getvalue()
