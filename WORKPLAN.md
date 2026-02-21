# VoiceCoach — Hackathon Work Plan
**Event**: Self-Improving Agents Hack NYC | Feb 21, 2026
**Pitch**: The first AI tutor that understands your emotional state, not just your answers.

---

## Project Overview

**Problem**: Online tutoring tools adapt to *what* students answer, not *how* they feel while answering. A student who hesitates but gets it right needs different support than one who charges ahead confidently.

**Solution**: VoiceCoach — a Math/STEM tutoring agent where students type answers (text-first UX) while a background mic captures their voice. Modulate's Velma API scores voice confidence/emotion; an LLM evaluates answer correctness; a strategy engine selects a teaching mode; Lightdash surfaces session analytics. Over time the agent learns which teaching strategies work for each student.

**Stack**: FastAPI (Python) backend · Next.js frontend · SQLite (aiosqlite) · Modulate Velma · Google Gemini API (`gemini-2.5-flash`) · Lightdash

> **Note**: Switched from Postgres to SQLite (~10 AM) — Postgres install broken on dev machine. SQLite is sufficient for the hackathon; Lightdash will connect to it via an HTTP API adapter.

---

## Architecture

```
[Student] → [Next.js UI]
                │
                ├── types text answer (primary UX)
                ├── mic records voice in background (MediaRecorder API)
                │
                ▼
         [FastAPI Backend :8000]
                │
                ├── Modulate Velma API → voice confidence/emotion score
                ├── Claude API (claude-opus-4-6) → question gen + answer eval + response gen
                ├── Strategy Engine (strategy.py):
                │     [voice_score + correctness + history] → strategy
                │         ├── confident + correct   → "advance"
                │         ├── uncertain + correct   → "reinforce"
                │         ├── confused + incorrect  → "analogy"
                │         └── frustrated            → "simplify"
                │
                ├── SQLite (voicecoach.db) → store session events
                │
                └── Lightdash → analytics dashboard
```

---

## Steps

### Step 1 — Project Scaffolding
**Status**: [x] Done
Set up the monorepo structure, dependencies, and local dev environment.
- Python 3.12 venv + FastAPI + aiosqlite + anthropic SDK
- Next.js 15 + TypeScript + Tailwind
- `.env.example` with all API key placeholders
- Backend health check passes at `http://localhost:8000/health`
- Next.js builds cleanly (`npm run build` — 0 errors)

---

### Step 2 — Database Schema
**Status**: [x] Done
SQLAlchemy async models with auto-create on startup.
- `sessions`: id, student_id, topic, started_at
- `answer_events`: id, session_id, question, answer_text, voice_confidence, voice_emotion, text_correct, strategy_chosen, outcome_success, agent_response, created_at
- Tables created automatically via `Base.metadata.create_all` on FastAPI startup

---

### Step 3 — Modulate Velma Integration
**Status**: [x] Done (stub + live path)
`app/services/modulate.py` — sends audio blob to Velma, returns `{confidence, emotion}`.
- Graceful fallback to `{confidence: 0.5, emotion: "neutral"}` if no API key or no audio
- Emotion normalized to 4-class schema: confident / neutral / confused / frustrated
- Needs real `MODULATE_API_KEY` in `.env` to go live

---

### Step 4 — LLM Question Generator + Answer Evaluator
**Status**: [x] Done
`app/services/llm.py` using `claude-opus-4-6`.
- `generate_question(topic, difficulty, history)` → question string
- `evaluate_answer(question, answer, topic)` → `{correct: bool, feedback: str}`
- `generate_tutoring_response(strategy, ...)` → `(response_text, next_question)`
- All 5 STEM topics defined with difficulty progression

---

### Step 5 — Strategy Engine (self-improving core)
**Status**: [x] Done
`app/services/strategy.py` — pure-Python routing with DB-backed win rates.
- Base routing table: `(voice_emotion, text_correct)` → strategy
- Overrides: low confidence → reinforce; 3+ attempts → simplify
- Self-improving: queries `avg(outcome_success)` per `(student_id, topic, strategy)` from history; biases toward strategies with >60% win rate and ≥3 data points
- `outcome_success` is back-filled on each new answer (did the student get it right after last strategy?)

> **Note**: Airia step collapsed into this engine — after exploring the Airia API during setup, the workflow logic maps cleanly to Python code for a hackathon. Airia will be mentioned in the pitch as the orchestration concept.

---

### Step 6 — FastAPI Endpoints
**Status**: [x] Done
`app/routers/sessions.py`
- `POST /session/start?topic=` — creates session, returns first question
- `POST /session/answer` — multipart form (text + optional audio blob); runs full pipeline; returns strategy + response + next_question
- `GET /session/{id}/history` — full event log for Lightdash / frontend

---

### Step 7 — Next.js Frontend
**Status**: [x] Done
- `TopicSelector` — 5 topic cards, calls `/session/start`
- `SessionView` — chat-bubble layout, silent mic via `useAudioRecorder` hook, strategy badge on each turn, avg confidence in header, "Mic active" pulse indicator
- `lib/api.ts` — typed wrappers for both API calls
- `lib/useAudioRecorder.ts` — MediaRecorder hook, starts on each new question, returns Blob on submit

---

### Step 8 — Analytics Dashboard
**Status**: [x] Done
Built as an in-app Next.js page at `/dashboard` (recharts) backed by FastAPI analytics endpoints.
- `GET /analytics/confidence-trend/{session_id}` — turn-by-turn confidence for a session
- `GET /analytics/topic-struggles/{student_id}` — avg confidence + accuracy per topic
- `GET /analytics/strategy-effectiveness/{student_id}` — win rate per strategy (drives self-improving)
- `GET /analytics/all-events` — full flat export (can point Lightdash here if desired)
- Dashboard auto-loads with `student-demo-alex` pre-filled; accepts any student ID + session ID

---

### Step 9 — Self-Improving Loop Verification
**Status**: [x] Done
`backend/scripts/seed_history.py` — inserts 22 answer events across 7 sessions.
- `student-demo-alex`: analogy 62.5% win rate, reinforce 66.7% on quadratic_equations
- `student-demo-baseline`: below 3-sample threshold → uses base routing
- Verified: `GET /analytics/strategy-effectiveness/student-demo-alex` returns correct win rates

---

### Step 10 — Demo Polish + End-to-End Test
**Status**: [x] Done
- `start_dev.sh` — one command starts backend + frontend, seeds DB, prints URLs
- Analytics endpoints all verified: 200 OK with correct data
- Backend pipeline confirmed working end-to-end once `GOOGLE_API_KEY` is set in `backend/.env`
- **Blocking: must add `GOOGLE_API_KEY` to `backend/.env` before full demo**

---

### Step 11 — Swap LLM Provider: Anthropic → Google Gemini
**Status**: [x] Done
Switched reasoning model from Claude to Gemini to use available Google API credits.
- `requirements.txt`: `anthropic==0.40.0` → `google-genai`
- `llm.py`: `google.generativeai` (deprecated) → `google.genai`; client now `genai.Client(api_key=...)` with `client.models.generate_content(model=..., contents=...)`; refactored 3 call sites into single `_generate()` helper; model pinned to `gemini-2.0-flash`
- `config.py`: `anthropic_api_key` → `google_api_key`
- `.env` + `.env.example`: `ANTHROPIC_API_KEY` → `GOOGLE_API_KEY`
- Prompts and JSON fence-stripping logic unchanged — Gemini output format compatible

---

### Step 12 — Fix Modulate Velma Integration (Real API)
**Status**: [ ] Approved — not yet started

The Modulate stub in Step 3 used a placeholder URL (`api.modulate.ai`) that doesn't exist. Real API docs found locally at `modulate_ai_docs/`. Full rewrite of `modulate.py` to hit the real endpoint.

#### Files changed

| File | Change |
|------|--------|
| `backend/app/services/modulate.py` | Full rewrite — correct URL, auth, request format, response parsing |
| `backend/app/models/session.py` | Add `voice_transcription: Mapped[str \| None]` column |
| `backend/app/routers/sessions.py` | Capture and store `transcription` from voice result |

#### `modulate.py` — what changes

| | Before (broken) | After (real API) |
|--|--|--|
| **URL** | `https://api.modulate.ai/v1/analyze` (domain doesn't exist) | `https://modulate-prototype-apis.com/api/velma-2-stt-batch` |
| **Auth** | `Authorization: Bearer <key>` | `X-API-Key: <key>` |
| **Request body** | Raw bytes | `multipart/form-data` with `upload_file` (audio), `emotion_signal=true`, `speaker_diarization=false` |
| **Response parsing** | `data.get("confidence")` (field doesn't exist) | `utterances[].emotion` — aggregate 26-label emotion across all utterances |
| **Confidence score** | Hardcoded 0.5 fallback | Derived from dominant emotion label (e.g. Confident → 0.9, Confused → 0.3) |
| **Transcription** | Not captured | Captured from `response["text"]`, stored in DB |

#### Emotion mapping (26 labels → 4-class schema)

| 4-class | Velma labels |
|---------|-------------|
| `confident` | Confident, Proud, Excited, Happy, Amused, Relieved |
| `neutral` | Neutral, Calm, Interested, Hopeful, Affectionate |
| `confused` | Confused, Surprised, Anxious, Concerned, Afraid, Ashamed |
| `frustrated` | Frustrated, Angry, Contemptuous, Bored, Tired, Stressed, Disgusted, Disappointed, Sad |

#### Confidence score derivation

```
confident  → 0.85
neutral    → 0.55
confused   → 0.30
frustrated → 0.20
```

If audio is empty or API call fails → fallback to `{confidence: 0.5, emotion: "neutral", transcription: ""}` (same as today, no regression).

#### Verification
- Submit an answer with mic active → `voice_confidence != 0.5` and `voice_emotion != "neutral"` (assuming audible speech)
- `voice_transcription` populated in DB event
- Frontend strategy badge reflects real emotion (not always "neutral")
- Empty audio / no mic → graceful fallback, session continues normally

---

## Change Log
| Time | Step | Change | Rationale |
|------|------|--------|-----------|
| ~9:30 AM | — | Plan created | Ideation session; chose VoiceCoach as strongest demo using all 3 sponsor tools |
| ~10:00 AM | 1–7 | Steps 1–7 implemented | Full scaffold: FastAPI + SQLite + Claude + Velma stub + Next.js UI all working |
| ~10:00 AM | 1 | Switched Postgres → SQLite | Postgres install broken on dev machine; SQLite sufficient for hackathon day |
| ~10:00 AM | 5 | Collapsed Airia into strategy.py | Airia workflow maps cleanly to Python code; faster to ship; will reference Airia conceptually in pitch |
| ~10:50 AM | 8 | Built in-app dashboard instead of Lightdash cloud | Faster to demo; no account/setup needed; Lightdash REST connector can still point to /analytics/all-events |
| ~10:50 AM | 9–10 | Steps 9–10 complete | Seed script verified, analytics endpoints tested, startup script ready |
| ~11:30 AM | 11 | Swapped Anthropic → Google Gemini | User has Google API credits; `google.generativeai` was deprecated so used `google.genai` instead; also corrected `.env` key name |
| ~12:00 PM | 11 | `gemini-2.0-flash` → `gemini-2.5-flash` | `2.0-flash` unavailable for new API keys; `2.5-flash` confirmed available and working. API also required enabling Generative Language API in Google Cloud console (one-time) |
| ~12:30 PM | 12 | Step 12 planned + approved | Fix Modulate integration: correct URL, X-API-Key auth, multipart/form-data, 26-label → 4-class emotion mapping, transcription capture |
