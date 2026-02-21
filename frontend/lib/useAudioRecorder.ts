"use client";

import { useRef, useCallback, useState } from "react";

/**
 * Silent background audio recorder using MediaRecorder.
 * Call startRecording() when a question appears, stopRecording() when the
 * student submits — returns the audio Blob.
 */
export function useAudioRecorder() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.start(100); // collect chunks every 100ms
      setIsRecording(true);
    } catch {
      // Mic permission denied or unavailable — silent fallback
      mediaRecorderRef.current = null;
      setIsRecording(false);
    }
  }, []);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setIsRecording(false);
        resolve(null);
        return;
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        // Stop all tracks to release the mic
        streamRef.current?.getTracks().forEach((t) => t.stop());
        setIsRecording(false);
        resolve(blob.size > 0 ? blob : null);
      };
      recorder.stop();
    });
  }, []);

  return { startRecording, stopRecording, isRecording };
}
