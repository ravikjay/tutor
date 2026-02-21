"""
seed_history.py — Pre-populate the DB with fake historical sessions.

This makes the self-improving loop demonstrable on day-of without needing
10 real sessions. Seeds 3 students × 2 topics with known strategy outcomes
so the selector visibly routes differently for seeded vs. new students.

Usage:
  cd backend
  .venv/bin/python scripts/seed_history.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, AsyncSessionLocal, Base
from app.models.session import Session, AnswerEvent


# ---------------------------------------------------------------------------
# Seed data: (student_id_suffix, topic, strategy, outcome_success, n_events)
# We'll insert n_events rows per (student, topic, strategy) with the given
# success rate so the selector's win-rate query has data to work with.
# ---------------------------------------------------------------------------
SEED_PROFILES = [
    # Demo student: "analogy" works great for them on quadratic_equations
    {
        "student_suffix": "demo-alex",
        "topic": "quadratic_equations",
        "strategy_outcomes": [
            ("analogy",   True,  5),   # 5 successes with analogy
            ("reinforce", False, 3),   # 3 failures with reinforce
            ("simplify",  False, 2),   # 2 failures with simplify
        ],
    },
    # Demo student: "reinforce" works great for them on derivatives
    {
        "student_suffix": "demo-alex",
        "topic": "derivatives",
        "strategy_outcomes": [
            ("reinforce", True,  6),
            ("analogy",   False, 3),
        ],
    },
    # Control student: no strong pattern — base routing will apply
    {
        "student_suffix": "demo-baseline",
        "topic": "quadratic_equations",
        "strategy_outcomes": [
            ("analogy",   True,  2),   # only 2 — below the 3-sample threshold
            ("reinforce", True,  1),
        ],
    },
]

DEMO_QUESTIONS = [
    "What is a quadratic equation? Explain in your own words.",
    "How do you find the roots of x² - 5x + 6 = 0?",
    "What does the discriminant tell you?",
    "What is the derivative of x²?",
    "Explain the chain rule with an example.",
    "What does it mean for a function to be differentiable?",
]

DEMO_ANSWERS = [
    "It's an equation with x squared in it.",
    "You factor it: (x-2)(x-3) so x=2 or x=3.",
    "It tells you how many real solutions there are.",
    "The derivative of x² is 2x.",
    "You multiply the outer and inner derivatives together.",
    "It means the limit of the slope exists at that point.",
]


async def seed():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        inserted_sessions = 0
        inserted_events = 0

        for profile in SEED_PROFILES:
            student_id = f"student-{profile['student_suffix']}"

            for strategy, outcome, n in profile["strategy_outcomes"]:
                # One session per (student, topic, strategy) batch
                session = Session(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    topic=profile["topic"],
                    started_at=datetime.utcnow() - timedelta(days=7),
                )
                db.add(session)
                await db.flush()
                inserted_sessions += 1

                for i in range(n):
                    q_idx = i % len(DEMO_QUESTIONS)
                    a_idx = i % len(DEMO_ANSWERS)
                    event = AnswerEvent(
                        id=str(uuid.uuid4()),
                        session_id=session.id,
                        question=DEMO_QUESTIONS[q_idx],
                        answer_text=DEMO_ANSWERS[a_idx],
                        voice_confidence=0.8 if outcome else 0.3,
                        voice_emotion="confident" if outcome else "confused",
                        text_correct=outcome,
                        strategy_chosen=strategy,
                        outcome_success=outcome,
                        agent_response="[seeded]",
                        created_at=datetime.utcnow() - timedelta(days=7 - i),
                    )
                    db.add(event)
                    inserted_events += 1

        await db.commit()
        print(f"Seeded {inserted_sessions} sessions, {inserted_events} answer events.")
        print()
        print("Demo student IDs:")
        print("  student-demo-alex     → prefers 'analogy' on quadratic_equations")
        print("                        → prefers 'reinforce' on derivatives")
        print("  student-demo-baseline → no strong pattern (below threshold)")
        print()
        print("To see self-improving routing in action:")
        print("  POST /session/start?topic=quadratic_equations with student_id=student-demo-alex")
        print("  Then submit a confused answer — it should route to 'analogy' immediately.")


if __name__ == "__main__":
    asyncio.run(seed())
