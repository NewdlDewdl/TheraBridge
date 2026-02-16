"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface PipelineEvent {
  timestamp: string;
  patient_id: string;
  phase: "TRANSCRIPT" | "WAVE1" | "WAVE2";
  event: string;
  status: string;
  session_id?: string;
  session_date?: string;
  duration_ms?: number;
  details?: Record<string, any>;
}

interface UsePipelineEventsOptions {
  patientId: string;
  enabled?: boolean;
  onEvent?: (event: PipelineEvent) => void;
  onWave1SessionComplete?: (sessionId: string, sessionDate: string) => void;
  onWave2SessionComplete?: (sessionId: string, sessionDate: string) => void;
}

interface UsePipelineEventsReturn {
  isConnected: boolean;
  connectionError: string | null;
  errorType: 'none' | 'patient_not_found' | 'cors' | 'network' | 'unknown';
  events: PipelineEvent[];
  latestEvent: PipelineEvent | null;
}

export function usePipelineEvents(options: UsePipelineEventsOptions) {
  const {
    patientId,
    enabled = true,
    onEvent,
    onWave1SessionComplete,
    onWave2SessionComplete,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'none' | 'patient_not_found' | 'cors' | 'network' | 'unknown'>('none');
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const handleEventRef = useRef<(event: PipelineEvent) => void>();

  const handleEvent = useCallback(
    (event: PipelineEvent) => {
      // Add to events list
      setEvents((prev) => [...prev, event]);

      // Call custom event handler
      if (onEvent) {
        onEvent(event);
      }

      // Detect Wave 1 session completion
      if (
        event.phase === "WAVE1" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 1 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave1SessionComplete) {
          onWave1SessionComplete(event.session_id, event.session_date);
        }
      }

      // Detect Wave 2 session completion
      if (
        event.phase === "WAVE2" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 2 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave2SessionComplete) {
          onWave2SessionComplete(event.session_id, event.session_date);
        }
      }
    },
    [onEvent, onWave1SessionComplete, onWave2SessionComplete]
  );

  // Update ref when handleEvent changes
  useEffect(() => {
    handleEventRef.current = handleEvent;
  }, [handleEvent]);

  useEffect(() => {
    if (!enabled || !patientId) {
      console.log('[SSE] Connection disabled or no patient ID');

      // Clean up existing connection if patient ID was cleared
      if (eventSourceRef.current) {
        console.log('[SSE] Patient ID cleared - disconnecting existing SSE');
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
        setConnectionError(null);
      }
      return;
    }

    // Check if this is a patient ID change (not initial mount)
    const previousPatientId = eventSourceRef.current?.url.split('/').pop();
    if (previousPatientId && previousPatientId !== patientId && eventSourceRef.current) {
      console.log(`[SSE] Patient ID changed: ${previousPatientId} → ${patientId}`);
      console.log('[SSE] Disconnecting from old patient...');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setConnectionError(null);
    }

    console.log(`[SSE] Connecting to patient ${patientId}...`);

    // Create EventSource connection
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const sseUrl = `${apiUrl}/api/sse/events/${patientId}`;

    console.log(`[SSE] URL: ${sseUrl}`);

    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log(`📡 SSE connected to patient ${patientId}`);
      setIsConnected(true);
      setConnectionError(null);
      setErrorType('none');
    };

    eventSource.onmessage = (messageEvent) => {
      try {
        const event: PipelineEvent = JSON.parse(messageEvent.data);
        // Use ref to avoid stale closure
        if (handleEventRef.current) {
          handleEventRef.current(event);
        }
      } catch (error) {
        console.error("[SSE] Failed to parse event:", error);
        console.error("[SSE] Raw data:", messageEvent.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      setIsConnected(false);
      // Don't close - let browser handle reconnection
    };

    // Cleanup on unmount or patient ID change
    return () => {
      console.log(`📡 SSE disconnected from patient ${patientId}`);
      eventSource.close();
      setIsConnected(false);
      setConnectionError(null);
    };
  }, [enabled, patientId]);  // Removed handleEvent to prevent reconnection loop

  return {
    isConnected,
    connectionError,
    errorType,
    events,
    latestEvent: events[events.length - 1] || null,
  };
}
