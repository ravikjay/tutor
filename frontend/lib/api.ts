const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type StartResponse = {
  session_id: string;
  student_id: string;
  topic: string;
  topic_label: string;
  question: string;
};

export type AnswerResponse = {
  voice_confidence: number;
  voice_emotion: string;
  voice_transcription: string;
  text_correct: boolean;
  strategy: string;
  agent_response: string;
  next_question: string;
  event_id: string;
};

export async function startSession(topic: string): Promise<StartResponse> {
  const res = await fetch(`${API}/session/start?topic=${topic}`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitAnswer(
  sessionId: string,
  question: string,
  answerText: string,
  audioBlob: Blob | null,
): Promise<AnswerResponse> {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("question", question);
  form.append("answer_text", answerText);
  if (audioBlob && audioBlob.size > 0) {
    form.append("audio", audioBlob, "answer.webm");
  }
  const res = await fetch(`${API}/session/answer`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
