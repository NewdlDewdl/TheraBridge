"use client";

/**
 * WaveCompletionBridge - SSE-based Real-Time Updates
 *
 * Connects to SSE endpoint and triggers per-session updates as they complete.
 *
 * Behavior:
 *   - Waits for patient ID to exist in localStorage before connecting
 *   - Connects to SSE stream on mount
 *   - When Wave 1 completes for a session: triggers loading state + refresh for that session
 *   - When Wave 2 completes for a session: triggers loading state + refresh for that session
 *   - Disconnects when all analysis complete
 *   - Automatically reconnects on simple refresh (preserves patient ID)
 */

import { useEffect, useState } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { demoTokenStorage } from "@/lib/demo-token-storage";
import { POLLING_CONFIG, logPolling } from "@/lib/polling-config";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  // Continuously poll for patient ID - detects when it changes or gets cleared (hard refresh)
  useEffect(() => {
    const checkPatientId = () => {
      const id = demoTokenStorage.getPatientId();
      const initStatus = demoTokenStorage.getInitStatus();

      // Patient ID exists - set it and mark as ready
      if (id) {
        // Only log if patient ID changed
        if (id !== patientId) {
          console.log('[WaveCompletionBridge] ✓ Patient ID found:', id);
        }
        setPatientId(id);
        setIsReady(true);
        setIsInitializing(false);
        return;
      }

      // No patient ID - check if we need to initialize
      if (!id && patientId) {
        // Patient ID was cleared (hard refresh!)
        console.log('[WaveCompletionBridge] Patient ID cleared - resetting state');
        setPatientId(null);
        setIsReady(false);
        setIsInitializing(false);
        return;
      }

      // No patient ID and initialization pending
      if (initStatus === 'pending') {
        if (!isInitializing) {
          console.log('[WaveCompletionBridge] Demo initialization in progress...');
          setIsInitializing(true);
        }
        return;
      }

      // No patient ID and no initialization - trigger it
      if (initStatus === 'none' && !isInitializing && !patientId) {
        console.log('[WaveCompletionBridge] Triggering demo initialization...');
        setIsInitializing(true);

        // Import and call demo initialization
        import('@/lib/demo-api-client').then(({ demoApiClient }) => {
          demoApiClient.initialize().catch(err => {
            console.error('[WaveCompletionBridge] Demo init failed:', err);
            setIsInitializing(false);
          });
        });
      }
    };

    // Check immediately
    checkPatientId();

    // Poll every 500ms continuously
    const interval = setInterval(checkPatientId, 500);

    return () => clearInterval(interval);
  }, [patientId, isInitializing]); // Re-run when patient ID or init state changes

  // Connect to SSE and handle events (only after we have patient ID)
  const { isConnected, events, errorType, connectionError } = usePipelineEvents({
    patientId: patientId || "",
    enabled: isReady && !!patientId,

    onWave1SessionComplete: async (sessionId, sessionDate) => {
      if (!POLLING_CONFIG.sseEnabled) {
        logPolling('[SSE] SSE disabled via feature flag, ignoring event');
        return;
      }

      logPolling(`[SSE] Wave 1 complete for session ${sessionDate} (${sessionId})`);

      // Show loading overlay immediately (no stagger for real-time)
      setSessionLoading(sessionId, true);

      // Fetch updated session data
      await refresh();

      // Hide loading overlay after duration + fade
      setTimeout(() => {
        setSessionLoading(sessionId, false);
      }, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration);
    },

    onWave2SessionComplete: async (sessionId, sessionDate) => {
      if (!POLLING_CONFIG.sseEnabled) {
        logPolling('[SSE] SSE disabled via feature flag, ignoring event');
        return;
      }

      logPolling(`[SSE] Wave 2 complete for session ${sessionDate} (${sessionId})`);

      // Show loading overlay immediately (no stagger for real-time)
      setSessionLoading(sessionId, true);

      // Fetch updated session data
      await refresh();

      // Hide loading overlay after duration + fade
      setTimeout(() => {
        setSessionLoading(sessionId, false);
      }, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration);
    },
  });

  // Log connection status
  useEffect(() => {
    if (isConnected && patientId) {
      console.log(`📡 SSE connected to patient ${patientId} - listening for pipeline events`);
    }
  }, [isConnected, patientId]);

  // Log events for debugging
  useEffect(() => {
    if (events.length > 0) {
      const latest = events[events.length - 1];
      console.log(
        `[${latest.phase}] ${latest.session_date || "N/A"} - ${latest.event}`,
        latest.details || ""
      );
    }
  }, [events]);

  // Log error state changes
  useEffect(() => {
    if (errorType !== 'none' && connectionError) {
      console.group('[WaveCompletionBridge] SSE Error Detected');
      console.error('Error type:', errorType);
      console.error('Error message:', connectionError);
      console.log('Patient ID:', patientId);
      console.log('Is ready:', isReady);
      console.groupEnd();

      // If patient not found, patient ID may be stale
      if (errorType === 'patient_not_found' && patientId) {
        console.warn('[WaveCompletionBridge] Patient not found - may need to reinitialize demo');
      }
    }
  }, [errorType, connectionError, patientId, isReady]);

  return null;
}
