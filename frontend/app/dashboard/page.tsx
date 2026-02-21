"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Legend,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STRATEGY_COLORS: Record<string, string> = {
  advance:   "#22c55e",
  reinforce: "#3b82f6",
  analogy:   "#f59e0b",
  simplify:  "#a855f7",
};

type Event = {
  student_id: string;
  topic: string;
  voice_confidence: number;
  voice_emotion: string;
  text_correct: boolean;
  strategy_chosen: string;
  outcome_success: boolean | null;
  created_at: string;
};

export default function Dashboard() {
  const [studentId, setStudentId] = useState("student-demo-alex");
  const [sessionId, setSessionId] = useState("");
  const [events, setEvents] = useState<Event[]>([]);
  const [topicData, setTopicData] = useState<any[]>([]);
  const [strategyData, setStrategyData] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);

  async function load() {
    const [eventsRes, topicRes, stratRes] = await Promise.all([
      fetch(`${API}/analytics/all-events`),
      fetch(`${API}/analytics/topic-struggles/${studentId}`),
      fetch(`${API}/analytics/strategy-effectiveness/${studentId}`),
    ]);
    const evs: Event[] = await eventsRes.json();
    setEvents(evs);
    setTopicData(await topicRes.json());
    setStrategyData(await stratRes.json());

    // If session ID provided, load confidence trend
    if (sessionId) {
      const trendRes = await fetch(`${API}/analytics/confidence-trend/${sessionId}`);
      setTrend(await trendRes.json());
    }
  }

  useEffect(() => { load(); }, [studentId, sessionId]);

  const recentEvents = events
    .filter((e) => e.student_id === studentId)
    .slice(-20)
    .map((e, i) => ({ turn: i + 1, confidence: Math.round((e.voice_confidence || 0) * 100), strategy: e.strategy_chosen, emotion: e.voice_emotion }));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">VoiceCoach Analytics</h1>
            <p className="text-gray-500 text-sm mt-1">Powered by self-improving session data</p>
          </div>
          <a href="/" className="text-sm text-indigo-600 underline">← Back to tutor</a>
        </div>

        {/* Controls */}
        <div className="flex gap-4 flex-wrap">
          <div>
            <label className="text-xs font-semibold text-gray-500 block mb-1">Student ID</label>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 block mb-1">Session ID (for trend)</label>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-80"
              placeholder="paste session_id from /session/start"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
            />
          </div>
          <button
            onClick={load}
            className="self-end bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700"
          >
            Refresh
          </button>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total answers" value={events.filter(e => e.student_id === studentId).length} />
          <StatCard
            label="Avg voice confidence"
            value={
              events.filter(e => e.student_id === studentId).length
                ? Math.round(events.filter(e => e.student_id === studentId).reduce((s, e) => s + (e.voice_confidence || 0), 0) / events.filter(e => e.student_id === studentId).length * 100) + "%"
                : "—"
            }
          />
          <StatCard
            label="Overall accuracy"
            value={
              events.filter(e => e.student_id === studentId).length
                ? Math.round(events.filter(e => e.student_id === studentId).filter(e => e.text_correct).length / events.filter(e => e.student_id === studentId).length * 100) + "%"
                : "—"
            }
          />
        </div>

        {/* Confidence trend (session) */}
        {trend.length > 0 && (
          <ChartCard title="Voice Confidence Trend (this session)" subtitle="How confidence changed turn-by-turn">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="turn" label={{ value: "Turn", position: "insideBottom", offset: -2 }} tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: unknown) => [`${Math.round((v as number) * 100)}%`]} />
                <Line type="monotone" dataKey="voice_confidence" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Recent confidence across all sessions */}
        {recentEvents.length > 0 && (
          <ChartCard title="Recent Voice Confidence (all sessions)" subtitle="Color = strategy chosen">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={recentEvents}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="turn" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: unknown) => [`${v}%`]} />
                <Bar dataKey="confidence" radius={[4, 4, 0, 0]}>
                  {recentEvents.map((entry, i) => (
                    <Cell key={i} fill={STRATEGY_COLORS[entry.strategy] ?? "#94a3b8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-4 mt-2 flex-wrap">
              {Object.entries(STRATEGY_COLORS).map(([s, c]) => (
                <span key={s} className="flex items-center gap-1 text-xs text-gray-500">
                  <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: c }} />
                  {s}
                </span>
              ))}
            </div>
          </ChartCard>
        )}

        {/* Topic struggles */}
        {topicData.length > 0 && (
          <ChartCard title="Topic Confidence Breakdown" subtitle="Where does this student struggle most?">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={topicData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="topic" tick={{ fontSize: 11 }} width={140} />
                <Tooltip formatter={(v: unknown) => [`${Math.round((v as number) * 100)}%`]} />
                <Bar dataKey="avg_confidence" name="Avg Confidence" fill="#6366f1" radius={[0, 4, 4, 0]} />
                <Bar dataKey="accuracy" name="Accuracy" fill="#22c55e" radius={[0, 4, 4, 0]} />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        )}

        {/* Strategy effectiveness */}
        {strategyData.length > 0 && (
          <ChartCard title="Strategy Effectiveness" subtitle="Win rate per teaching strategy — this drives self-improvement">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={strategyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="strategy" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v: unknown, _: unknown, p: any) =>
                    [`${Math.round((v as number) * 100)}% (n=${p.payload.sample_size})`, "Win rate"]
                  }
                />
                <Bar dataKey="win_rate" radius={[6, 6, 0, 0]}>
                  {strategyData.map((entry, i) => (
                    <Cell key={i} fill={STRATEGY_COLORS[entry.strategy] ?? "#94a3b8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-2">
              Strategies with &gt;60% win rate and ≥3 samples override the default routing for this student.
            </p>
          </ChartCard>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h2 className="font-semibold text-gray-800">{title}</h2>
      <p className="text-xs text-gray-400 mb-4">{subtitle}</p>
      {children}
    </div>
  );
}
