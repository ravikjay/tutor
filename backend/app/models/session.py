import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list["AnswerEvent"]] = relationship("AnswerEvent", back_populates="session")


class AnswerEvent(Base):
    __tablename__ = "answer_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=True)
    voice_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_emotion: Mapped[str | None] = mapped_column(String, nullable=True)
    voice_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    strategy_chosen: Mapped[str | None] = mapped_column(String, nullable=True)
    # outcome: did student answer correctly on the NEXT attempt after this strategy?
    outcome_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    agent_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship("Session", back_populates="events")
