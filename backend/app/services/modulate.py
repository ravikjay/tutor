"""
Modulate Velma API integration.
Sends audio blob to Velma-2 STT Batch, returns voice confidence + emotion + transcription.
Falls back to neutral defaults if API key not configured or on any error.
"""
import httpx
from app.config import settings

VELMA_API_URL = "https://modulate-prototype-apis.com/api/velma-2-stt-batch"

# 26-label Velma emotion → 4-class schema
_CONFIDENT_LABELS = {"Confident", "Proud", "Excited", "Happy", "Amused", "Relieved"}
_NEUTRAL_LABELS = {"Neutral", "Calm", "Interested", "Hopeful", "Affectionate"}
_CONFUSED_LABELS = {"Confused", "Surprised", "Anxious", "Concerned", "Afraid", "Ashamed"}
_FRUSTRATED_LABELS = {
    "Frustrated", "Angry", "Contemptuous", "Bored", "Tired",
    "Stressed", "Disgusted", "Disappointed", "Sad",
}

_CONFIDENCE_BY_CLASS = {
    "confident": 0.85,
    "neutral": 0.55,
    "confused": 0.30,
    "frustrated": 0.20,
}

_FALLBACK = {"confidence": 0.5, "emotion": "neutral", "transcription": ""}


def _velma_label_to_class(label: str) -> str:
    if label in _CONFIDENT_LABELS:
        return "confident"
    if label in _CONFUSED_LABELS:
        return "confused"
    if label in _FRUSTRATED_LABELS:
        return "frustrated"
    return "neutral"


def _aggregate_emotion(utterances: list[dict]) -> str:
    """Pick the most-frequent 4-class emotion across all utterances."""
    counts: dict[str, int] = {}
    for u in utterances:
        raw = u.get("emotion") or ""
        cls = _velma_label_to_class(raw)
        counts[cls] = counts.get(cls, 0) + 1
    if not counts:
        return "neutral"
    return max(counts, key=lambda k: counts[k])


async def analyze_voice(audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
    """
    Send audio to Velma and return {confidence, emotion, transcription}.
    confidence: 0.0–1.0
    emotion: "confident" | "neutral" | "confused" | "frustrated"
    transcription: full transcript string
    """
    if not settings.modulate_api_key or not audio_bytes:
        return _FALLBACK.copy()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                VELMA_API_URL,
                headers={"X-API-Key": settings.modulate_api_key},
                files={"upload_file": ("audio.webm", audio_bytes, mime_type)},
                data={"emotion_signal": "true", "speaker_diarization": "false"},
            )
            resp.raise_for_status()
            data = resp.json()

        transcription = data.get("text", "")
        utterances = data.get("utterances", [])
        emotion = _aggregate_emotion(utterances)
        confidence = _CONFIDENCE_BY_CLASS[emotion]

        return {"confidence": confidence, "emotion": emotion, "transcription": transcription}

    except Exception:
        return _FALLBACK.copy()
