"use client";

import { useState } from "react";
import { startSession, StartResponse } from "@/lib/api";

const TOPICS = [
  { key: "quadratic_equations", label: "Quadratic Equations", emoji: "📐" },
  { key: "derivatives", label: "Derivatives & Differentiation", emoji: "📈" },
  { key: "newtons_laws", label: "Newton's Laws of Motion", emoji: "🍎" },
  { key: "probability", label: "Probability & Statistics", emoji: "🎲" },
  { key: "linear_algebra", label: "Linear Algebra Basics", emoji: "🔢" },
];

type Props = { onSessionStart: (s: StartResponse) => void };

export default function TopicSelector({ onSessionStart }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleSelect(topicKey: string) {
    setLoading(topicKey);
    setError("");
    try {
      const session = await startSession(topicKey);
      onSessionStart(session);
    } catch (e) {
      setError("Failed to start session. Is the backend running?" + JSON.stringify(e));
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center p-6">
      <div className="max-w-xl w-full">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">VoiceCoach</h1>
          <p className="text-gray-500 text-lg">
            An AI tutor that listens to <em>how</em> you think, not just what you answer.
          </p>
        </div>

        <p className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4 text-center">
          Choose a topic to start
        </p>

        <div className="grid gap-3">
          {TOPICS.map((t) => (
            <button
              key={t.key}
              onClick={() => handleSelect(t.key)}
              disabled={!!loading}
              className="flex items-center gap-4 p-4 bg-white rounded-2xl border border-gray-200 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all text-left disabled:opacity-50"
            >
              <span className="text-3xl">{t.emoji}</span>
              <span className="text-gray-800 font-medium">{t.label}</span>
              {loading === t.key && (
                <span className="ml-auto text-indigo-500 text-sm animate-pulse">Starting...</span>
              )}
            </button>
          ))}
        </div>

        {error && (
          <p className="mt-4 text-red-500 text-sm text-center">{error}</p>
        )}

        <p className="mt-8 text-xs text-gray-400 text-center">
          Your microphone will be used to analyze your voice confidence — no audio is stored.
        </p>
      </div>
    </div>
  );
}
