"use client";

import { useState, useEffect, useRef } from "react";
import { submitAnswer, AnswerResponse } from "@/lib/api";
import { useAudioRecorder } from "@/lib/useAudioRecorder";
import { SessionData } from "@/app/page";

const STRATEGY_LABELS: Record<string, { label: string; color: string; description: string }> = {
  advance:   { label: "Advancing",        color: "bg-green-100 text-green-800",  description: "Great work! Moving to a harder concept." },
  reinforce: { label: "Reinforcing",      color: "bg-blue-100 text-blue-800",    description: "Let's solidify this before moving on." },
  analogy:   { label: "Trying an analogy", color: "bg-amber-100 text-amber-800", description: "Switching to a different explanation approach." },
  simplify:  { label: "Simplifying",      color: "bg-purple-100 text-purple-800", description: "Breaking it down to the core idea." },
};

const EMOTION_META: Record<string, { emoji: string; label: string; color: string }> = {
  confident:  { emoji: "😊", label: "Confident",  color: "text-green-700"  },
  neutral:    { emoji: "😐", label: "Neutral",    color: "text-gray-500"   },
  confused:   { emoji: "🤔", label: "Confused",   color: "text-amber-600"  },
  frustrated: { emoji: "😤", label: "Frustrated", color: "text-red-600"    },
};

// Animated waveform — 5 bars with staggered CSS animations
function VoiceWaveform() {
  const bars = [
    { height: "h-3", delay: "0ms",    duration: "600ms"  },
    { height: "h-5", delay: "100ms",  duration: "500ms"  },
    { height: "h-7", delay: "50ms",   duration: "700ms"  },
    { height: "h-5", delay: "150ms",  duration: "550ms"  },
    { height: "h-3", delay: "75ms",   duration: "650ms"  },
  ];

  return (
    <span className="inline-flex items-center gap-[3px] h-7">
      {bars.map((b, i) => (
        <span
          key={i}
          className={`w-[3px] ${b.height} rounded-full bg-red-400 animate-bounce`}
          style={{ animationDelay: b.delay, animationDuration: b.duration }}
        />
      ))}
    </span>
  );
}

type Turn = {
  question: string;
  answer: string;
  response: AnswerResponse;
};

type Props = {
  session: SessionData;
  onReset: () => void;
};

export default function SessionView({ session, onReset }: Props) {
  const [currentQuestion, setCurrentQuestion] = useState(session.question);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [latestResponse, setLatestResponse] = useState<AnswerResponse | null>(null);
  const { startRecording, stopRecording, isRecording } = useAudioRecorder();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  // Start recording as soon as the question appears
  useEffect(() => {
    startRecording();
    textareaRef.current?.focus();
  }, [currentQuestion]);

  // Scroll feed to bottom on new turns
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  async function handleSubmit() {
    if (!answer.trim() || loading) return;
    setLoading(true);

    const audioBlob = await stopRecording();

    try {
      const result = await submitAnswer(
        session.session_id,
        currentQuestion,
        answer.trim(),
        audioBlob,
      );
      setTurns((prev) => [
        ...prev,
        { question: currentQuestion, answer: answer.trim(), response: result },
      ]);
      setLatestResponse(result);
      setCurrentQuestion(result.next_question);
      setAnswer("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const strategy = latestResponse ? STRATEGY_LABELS[latestResponse.strategy] : null;
  const avgConfidence =
    turns.length > 0
      ? turns.reduce((s, t) => s + t.response.voice_confidence, 0) / turns.length
      : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white shadow-sm">
        <div>
          <h1 className="font-bold text-gray-900">VoiceCoach</h1>
          <p className="text-xs text-gray-400">{session.topic_label}</p>
        </div>
        <div className="flex items-center gap-4">
          {avgConfidence !== null && (
            <div className="text-xs text-gray-500">
              Avg confidence:{" "}
              <span className="font-semibold text-indigo-600">
                {Math.round(avgConfidence * 100)}%
              </span>
            </div>
          )}
          {/* Waveform / mic indicator */}
          <span className="inline-flex items-center gap-2 text-xs text-red-400 font-medium">
            {isRecording ? (
              <>
                <VoiceWaveform />
                <span>Listening…</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-gray-300" />
                <span className="text-gray-400">Mic off</span>
              </>
            )}
          </span>
          <a
            href="/dashboard"
            target="_blank"
            className="text-xs text-indigo-500 hover:text-indigo-700 underline"
          >
            Analytics
          </a>
          <button
            onClick={onReset}
            className="text-xs text-gray-400 hover:text-gray-700 underline"
          >
            New topic
          </button>
        </div>
      </header>

      {/* Turn feed */}
      <div ref={feedRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-2xl mx-auto w-full">
        {turns.map((turn, i) => {
          const emotionMeta = EMOTION_META[turn.response.voice_emotion] ?? EMOTION_META.neutral;
          return (
            <div key={i} className="space-y-3">
              {/* Question bubble */}
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">AI</div>
                <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-700 text-sm max-w-prose">
                  {turn.question}
                </div>
              </div>
              {/* Student answer */}
              <div className="flex gap-3 justify-end">
                <div className="space-y-1 items-end flex flex-col">
                  <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm max-w-prose">
                    {turn.answer}
                  </div>
                  {/* Voice analysis pill */}
                  <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-gray-100 border border-gray-200">
                    <span>{emotionMeta.emoji}</span>
                    <span className={`font-semibold ${emotionMeta.color}`}>{emotionMeta.label}</span>
                    <span className="text-gray-300">·</span>
                    <span className="text-gray-500">{Math.round(turn.response.voice_confidence * 100)}% confident</span>
                  </span>
                </div>
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 text-xs font-bold flex-shrink-0">You</div>
              </div>
              {/* Strategy badge + agent response */}
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">AI</div>
                <div className="space-y-2 max-w-prose">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-1 rounded-full ${STRATEGY_LABELS[turn.response.strategy]?.color}`}>
                    {STRATEGY_LABELS[turn.response.strategy]?.label}
                  </span>
                  <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-700 text-sm">
                    {turn.response.agent_response}
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {/* Current question */}
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">AI</div>
          <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-800 font-medium max-w-prose">
            {currentQuestion}
          </div>
        </div>
      </div>

      {/* Strategy hint banner */}
      {strategy && (
        <div className={`mx-6 mb-2 max-w-2xl mx-auto w-full`}>
          <div className={`px-4 py-2 rounded-xl text-xs font-medium ${strategy.color}`}>
            {strategy.description}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <div className="max-w-2xl mx-auto flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Type your answer here... (Enter to submit)"
            rows={3}
            className="flex-1 resize-none rounded-2xl border border-gray-300 px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !answer.trim()}
            className="h-12 px-5 bg-indigo-600 text-white rounded-2xl font-semibold text-sm hover:bg-indigo-700 disabled:opacity-40 transition-colors"
          >
            {loading ? "..." : "Submit"}
          </button>
        </div>
      </div>
    </div>
  );
}
