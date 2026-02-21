"""
Strategy selection engine — the "self-improving" core.

Chooses a teaching strategy based on:
  - voice_confidence (0.0-1.0 from Velma)
  - voice_emotion (confident / neutral / confused / frustrated)
  - text_correct (bool from LLM evaluator)
  - topic + historical win rates from the DB

Over time, win rates per (topic, strategy) are stored in answer_events.outcome_success.
The selector biases toward strategies that have historically worked for this student.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.session import AnswerEvent

STRATEGIES = ["advance", "reinforce", "analogy", "simplify"]

# Base routing table: (voice_emotion, text_correct) → preferred strategy
BASE_ROUTING = {
    ("confident", True):  "advance",
    ("neutral",   True):  "reinforce",
    ("confused",  True):  "reinforce",
    ("frustrated", True): "reinforce",
    ("confident", False): "analogy",
    ("neutral",   False): "analogy",
    ("confused",  False): "analogy",
    ("frustrated", False): "simplify",
}


async def select_strategy(
    db: AsyncSession,
    student_id: str,
    topic: str,
    voice_confidence: float,
    voice_emotion: str,
    text_correct: bool,
    attempts_on_topic: int,
) -> str:
    """Return the best strategy for this moment, biased by historical win rates."""
    base = BASE_ROUTING.get((voice_emotion, text_correct), "analogy")

    # If very low confidence override to simplify even if technically correct
    if voice_confidence < 0.3 and text_correct:
        base = "reinforce"

    # If many attempts and still wrong, escalate to simplify
    if attempts_on_topic >= 3 and not text_correct:
        base = "simplify"

    # Self-improving: check if history suggests a better strategy for this student+topic
    win_rates = await _get_win_rates(db, student_id, topic)
    if win_rates:
        best_historical = max(win_rates, key=win_rates.get)
        # Only override base if the historical winner is meaningfully better (>60% win rate)
        if win_rates.get(best_historical, 0) > 0.6 and best_historical != base:
            return best_historical

    return base


async def _get_win_rates(db: AsyncSession, student_id: str, topic: str) -> dict[str, float]:
    """Return win rate per strategy for this student+topic from historical sessions."""
    # Join answer_events → sessions to filter by student_id and topic
    from app.models.session import Session

    result = await db.execute(
        select(
            AnswerEvent.strategy_chosen,
            func.avg(AnswerEvent.outcome_success).label("win_rate"),
            func.count(AnswerEvent.id).label("n"),
        )
        .join(Session, AnswerEvent.session_id == Session.id)
        .where(
            Session.student_id == student_id,
            Session.topic == topic,
            AnswerEvent.strategy_chosen.isnot(None),
            AnswerEvent.outcome_success.isnot(None),
        )
        .group_by(AnswerEvent.strategy_chosen)
        .having(func.count(AnswerEvent.id) >= 3)  # need at least 3 data points
    )
    rows = result.fetchall()
    return {row.strategy_chosen: float(row.win_rate) for row in rows}
