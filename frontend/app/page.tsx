"use client";

import { useState } from "react";
import TopicSelector from "@/components/TopicSelector";
import SessionView from "@/components/SessionView";

export type SessionData = {
  session_id: string;
  student_id: string;
  topic: string;
  topic_label: string;
  question: string;
};

export default function Home() {
  const [session, setSession] = useState<SessionData | null>(null);

  if (!session) {
    return <TopicSelector onSessionStart={setSession} />;
  }

  return <SessionView session={session} onReset={() => setSession(null)} />;
}
