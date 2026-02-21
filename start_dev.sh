#!/bin/bash
# VoiceCoach — one-command dev startup
# Usage: ./start_dev.sh

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== VoiceCoach Dev Startup ==="

# Check .env
if [ ! -f "$ROOT/backend/.env" ]; then
  echo ""
  echo "ERROR: backend/.env not found."
  echo "  cp backend/.env.example backend/.env"
  echo "  then fill in GOOGLE_API_KEY"
  echo ""
  exit 1
fi

# Seed DB if empty
echo "→ Seeding historical data..."
cd "$ROOT/backend"
.venv/bin/python scripts/seed_history.py 2>/dev/null || true

# Start backend
echo "→ Starting FastAPI backend on :8000..."
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "→ Starting Next.js frontend on :3000..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Ready ==="
echo "  Tutor:     http://localhost:3000"
echo "  Dashboard: http://localhost:3000/dashboard"
echo "  API docs:  http://localhost:8000/docs"
echo ""
echo "Demo student IDs:"
echo "  student-demo-alex     (prefers 'analogy' on quadratic_equations)"
echo "  student-demo-baseline (no pattern — uses base routing)"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait
