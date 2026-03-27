"use client";

import { useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PipelineEvent {
  step: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
}

interface UsePipelineSSEOptions {
  projectId: string;
  enabled?: boolean;
}

interface UsePipelineSSEReturn {
  events: PipelineEvent[];
  isConnected: boolean;
  error: string | null;
}

export function usePipelineSSE({ projectId, enabled = true }: UsePipelineSSEOptions): UsePipelineSSEReturn {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled || !projectId) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const url = `${API_URL}/api/pipeline/${projectId}/events`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    es.onmessage = (event) => {
      try {
        const data: PipelineEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setError("Connection lost. Retrying...");
      setIsConnected(false);
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [projectId, enabled]);

  return { events, isConnected, error };
}
