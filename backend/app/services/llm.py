import google.genai as genai
from app.config import settings

_client = genai.Client(api_key=settings.google_api_key)
_MODEL = "gemini-2.5-flash"

TOPICS = {
    "quadratic_equations": "Quadratic Equations",
    "derivatives": "Derivatives & Differentiation",
    "newtons_laws": "Newton's Laws of Motion",
    "probability": "Probability & Statistics",
    "linear_algebra": "Linear Algebra Basics",
}


def _generate(prompt: str) -> str:
    """Single helper: call Gemini and return the text response."""
    response = _client.models.generate_content(model=_MODEL, contents=prompt)
    return response.text.strip()


def generate_question(topic: str, difficulty: int, history: list[dict]) -> str:
    """Generate a STEM question for the given topic and difficulty (1-5)."""
    prior = "\n".join(
        f"Q: {h['question']}\nA: {h['answer']}" for h in history[-3:]
    ) if history else "None yet."

    return _generate(
        f"You are a STEM tutor. Generate ONE question about '{topic}' "
        f"at difficulty level {difficulty}/5. "
        f"Keep it concise (1-2 sentences). Ask the student to explain "
        f"a concept in their own words or solve a small problem.\n\n"
        f"Prior Q&A in this session:\n{prior}\n\n"
        f"Return ONLY the question text, nothing else."
    )


def evaluate_answer(question: str, answer: str, topic: str) -> dict:
    """Evaluate student answer. Returns {correct: bool, feedback: str}."""
    import json
    raw = _generate(
        f"Topic: {topic}\n"
        f"Question: {question}\n"
        f"Student answer: {answer}\n\n"
        f"Evaluate whether the student's answer is correct or partially correct. "
        f"Respond in JSON with exactly these keys:\n"
        f'{{"correct": true/false, "feedback": "brief feedback in 1-2 sentences"}}'
    )
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_tutoring_response(
    strategy: str,
    question: str,
    answer: str,
    topic: str,
    feedback: str,
) -> tuple[str, str]:
    """
    Generate a tutoring response based on the chosen strategy.
    Returns (response_text, next_question).
    """
    import json

    strategy_instructions = {
        "advance": (
            "The student answered correctly and confidently. Praise them briefly, "
            "then move to a harder question on the same topic."
        ),
        "reinforce": (
            "The student answered correctly but sounded uncertain. Validate their answer, "
            "provide a concise reinforcing explanation to build confidence, "
            "then ask a similar question to solidify understanding."
        ),
        "analogy": (
            "The student is confused or got the answer wrong. Switch to a simple analogy "
            "or real-world example to explain the concept differently. Be encouraging. "
            "Then ask an easier version of the question."
        ),
        "simplify": (
            "The student seems frustrated. Be warm and encouraging. Break the concept "
            "down into the simplest possible terms. Ask a much simpler question."
        ),
    }

    instruction = strategy_instructions.get(strategy, strategy_instructions["reinforce"])

    raw = _generate(
        f"Topic: {topic}\n"
        f"You just asked: {question}\n"
        f"Student answered: {answer}\n"
        f"Your evaluation: {feedback}\n\n"
        f"Strategy: {instruction}\n\n"
        f"Respond in JSON with exactly these keys:\n"
        f'{{"response": "your tutoring response", "next_question": "the next question to ask"}}'
    )
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())
    return result["response"], result["next_question"]
