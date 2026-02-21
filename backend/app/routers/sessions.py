import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.session import Session, AnswerEvent
from app.services import llm, modulate, strategy
from app.services.llm import TOPICS

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start")
async def start_session(
    topic: str,
    student_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tutoring session and return the first question."""
    if topic not in TOPICS:
        raise HTTPException(400, f"Unknown topic. Choose from: {list(TOPICS.keys())}")

    sid = student_id or str(uuid.uuid4())
    session = Session(student_id=sid, topic=topic)
    db.add(session)
    await db.commit()

    question = llm.generate_question(TOPICS[topic], difficulty=1, history=[])
    return {
        "session_id": session.id,
        "student_id": sid,
        "topic": topic,
        "topic_label": TOPICS[topic],
        "question": question,
    }


@router.post("/answer")
async def submit_answer(
    session_id: str = Form(...),
    question: str = Form(...),
    answer_text: str = Form(...),
    audio: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept student's typed answer + optional audio blob.
    Runs Velma + LLM evaluator + strategy selector.
    Returns agent response and next question.
    """
    # Load session
    sess = await db.get(Session, session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    topic_label = TOPICS.get(sess.topic, sess.topic)

    # 1. Voice analysis (non-blocking fallback if no audio)
    audio_bytes = await audio.read() if audio else b""
    voice_result = await modulate.analyze_voice(audio_bytes)
    voice_confidence = voice_result["confidence"]
    voice_emotion = voice_result["emotion"]
    voice_transcription = voice_result.get("transcription", "")

    # 2. Text answer evaluation
    eval_result = llm.evaluate_answer(question, answer_text, topic_label)
    text_correct = eval_result["correct"]
    feedback = eval_result["feedback"]

    # 3. Count attempts on this topic in the current session
    attempts_result = await db.execute(
        select(func.count(AnswerEvent.id))
        .where(AnswerEvent.session_id == session_id)
    )
    attempts = attempts_result.scalar() or 0

    # 4. Strategy selection (self-improving)
    chosen_strategy = await strategy.select_strategy(
        db=db,
        student_id=sess.student_id,
        topic=sess.topic,
        voice_confidence=voice_confidence,
        voice_emotion=voice_emotion,
        text_correct=text_correct,
        attempts_on_topic=attempts,
    )

    # 5. Generate tutoring response + next question
    agent_response, next_question = llm.generate_tutoring_response(
        strategy=chosen_strategy,
        question=question,
        answer=answer_text,
        topic=topic_label,
        feedback=feedback,
    )

    # 6. Persist event
    event = AnswerEvent(
        session_id=session_id,
        question=question,
        answer_text=answer_text,
        voice_confidence=voice_confidence,
        voice_emotion=voice_emotion,
        voice_transcription=voice_transcription,
        text_correct=text_correct,
        strategy_chosen=chosen_strategy,
        agent_response=agent_response,
    )
    db.add(event)

    # 7. Update outcome_success on the previous event (did THIS answer succeed after last strategy?)
    prev_event_result = await db.execute(
        select(AnswerEvent)
        .where(
            AnswerEvent.session_id == session_id,
            AnswerEvent.outcome_success.is_(None),
            AnswerEvent.id != event.id,
        )
        .order_by(AnswerEvent.created_at.desc())
        .limit(1)
    )
    prev_event = prev_event_result.scalar_one_or_none()
    if prev_event:
        prev_event.outcome_success = text_correct

    await db.commit()

    return {
        "voice_confidence": voice_confidence,
        "voice_emotion": voice_emotion,
        "voice_transcription": voice_transcription,
        "text_correct": text_correct,
        "strategy": chosen_strategy,
        "agent_response": agent_response,
        "next_question": next_question,
        "event_id": event.id,
    }


@router.get("/{session_id}/history")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Return full event log for a session (used by Lightdash and frontend)."""
    sess = await db.get(Session, session_id)
    if not sess:
        raise HTTPException(404, "Session not found")

    result = await db.execute(
        select(AnswerEvent)
        .where(AnswerEvent.session_id == session_id)
        .order_by(AnswerEvent.created_at)
    )
    events = result.scalars().all()

    return {
        "session_id": session_id,
        "topic": sess.topic,
        "student_id": sess.student_id,
        "started_at": sess.started_at.isoformat(),
        "events": [
            {
                "id": e.id,
                "question": e.question,
                "answer_text": e.answer_text,
                "voice_confidence": e.voice_confidence,
                "voice_emotion": e.voice_emotion,
                "voice_transcription": e.voice_transcription,
                "text_correct": e.text_correct,
                "strategy_chosen": e.strategy_chosen,
                "agent_response": e.agent_response,
                "outcome_success": e.outcome_success,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }
