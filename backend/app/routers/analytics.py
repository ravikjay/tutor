"""
Analytics endpoints — powers both the in-app dashboard and Lightdash.

Lightdash can query these endpoints via its "Custom SQL" or REST connector.
The data is also consumed directly by the frontend's /dashboard page.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models.session import Session, AnswerEvent

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/confidence-trend/{session_id}")
async def confidence_trend(session_id: str, db: AsyncSession = Depends(get_db)):
    """Confidence score per answer turn for a single session."""
    result = await db.execute(
        select(
            AnswerEvent.id,
            AnswerEvent.voice_confidence,
            AnswerEvent.voice_emotion,
            AnswerEvent.strategy_chosen,
            AnswerEvent.text_correct,
            AnswerEvent.created_at,
        )
        .where(AnswerEvent.session_id == session_id)
        .order_by(AnswerEvent.created_at)
    )
    rows = result.fetchall()
    return [
        {
            "turn": i + 1,
            "voice_confidence": r.voice_confidence,
            "voice_emotion": r.voice_emotion,
            "strategy": r.strategy_chosen,
            "correct": r.text_correct,
            "timestamp": r.created_at.isoformat() if r.created_at else None,
        }
        for i, r in enumerate(rows)
    ]


@router.get("/topic-struggles/{student_id}")
async def topic_struggles(student_id: str, db: AsyncSession = Depends(get_db)):
    """Per-topic: avg confidence and accuracy for a student across all sessions."""
    result = await db.execute(
        select(
            Session.topic,
            func.avg(AnswerEvent.voice_confidence).label("avg_confidence"),
            func.avg(AnswerEvent.text_correct).label("accuracy"),
            func.count(AnswerEvent.id).label("total_answers"),
        )
        .join(AnswerEvent, AnswerEvent.session_id == Session.id)
        .where(Session.student_id == student_id)
        .group_by(Session.topic)
        .order_by(func.avg(AnswerEvent.voice_confidence))
    )
    rows = result.fetchall()
    return [
        {
            "topic": r.topic,
            "avg_confidence": round(float(r.avg_confidence or 0), 3),
            "accuracy": round(float(r.accuracy or 0), 3),
            "total_answers": r.total_answers,
        }
        for r in rows
    ]


@router.get("/strategy-effectiveness/{student_id}")
async def strategy_effectiveness(student_id: str, db: AsyncSession = Depends(get_db)):
    """Per-strategy: win rate (outcome_success) for a student across all sessions."""
    result = await db.execute(
        select(
            AnswerEvent.strategy_chosen,
            func.avg(AnswerEvent.outcome_success).label("win_rate"),
            func.count(AnswerEvent.id).label("n"),
        )
        .join(Session, AnswerEvent.session_id == Session.id)
        .where(
            Session.student_id == student_id,
            AnswerEvent.strategy_chosen.isnot(None),
            AnswerEvent.outcome_success.isnot(None),
        )
        .group_by(AnswerEvent.strategy_chosen)
        .order_by(func.avg(AnswerEvent.outcome_success).desc())
    )
    rows = result.fetchall()
    return [
        {
            "strategy": r.strategy_chosen,
            "win_rate": round(float(r.win_rate or 0), 3),
            "sample_size": r.n,
        }
        for r in rows
    ]


@router.get("/all-events")
async def all_events(db: AsyncSession = Depends(get_db)):
    """
    Flat export of all answer events joined with session metadata.
    This is the primary table Lightdash connects to — it can derive
    all three dashboard charts from this single endpoint.
    """
    result = await db.execute(
        select(
            Session.student_id,
            Session.topic,
            Session.started_at,
            AnswerEvent.id.label("event_id"),
            AnswerEvent.session_id,
            AnswerEvent.voice_confidence,
            AnswerEvent.voice_emotion,
            AnswerEvent.text_correct,
            AnswerEvent.strategy_chosen,
            AnswerEvent.outcome_success,
            AnswerEvent.created_at,
        )
        .join(AnswerEvent, AnswerEvent.session_id == Session.id)
        .order_by(AnswerEvent.created_at)
    )
    rows = result.fetchall()
    return [
        {
            "student_id": r.student_id,
            "topic": r.topic,
            "session_started_at": r.started_at.isoformat() if r.started_at else None,
            "event_id": r.event_id,
            "session_id": r.session_id,
            "voice_confidence": r.voice_confidence,
            "voice_emotion": r.voice_emotion,
            "text_correct": r.text_correct,
            "strategy_chosen": r.strategy_chosen,
            "outcome_success": r.outcome_success,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
