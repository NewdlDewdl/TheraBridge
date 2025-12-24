'use client';

/**
 * Demo Initialization Hook
 * Automatically initializes demo user on first visit
 */

import { useEffect, useState } from 'react';
import { demoTokenStorage } from '@/lib/demo-token-storage';
import { demoApiClient } from '@/lib/demo-api-client';

export function useDemoInitialization() {
  const [isInitializing, setIsInitializing] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [patientId, setPatientId] = useState<string | null>(null);

  useEffect(() => {
    const initializeDemo = async () => {
      console.log('[Demo Init] Checking demo status...');

      // Check if valid token exists
      if (demoTokenStorage.isInitialized()) {
        const existingPatientId = demoTokenStorage.getPatientId();
        console.log('[Demo Init] ✓ Valid token found, patient ID:', existingPatientId);
        setPatientId(existingPatientId);
        setIsReady(true);
        return;
      }

      // Token expired or doesn't exist - initialize new demo
      console.log('[Demo Init] No valid token, initializing new demo...');
      setIsInitializing(true);

      try {
        const result = await demoApiClient.initialize();

        if (result) {
          console.log('[Demo Init] ✓ Demo initialized:', result.patient_id);
          setPatientId(result.patient_id);
          setIsReady(true);
        } else {
          console.error('[Demo Init] ✗ Initialization failed');
          setIsReady(false);
        }
      } catch (error) {
        console.error('[Demo Init] Error:', error);
        setIsReady(false);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeDemo();
  }, []);

  return {
    isInitializing,
    isReady,
    patientId,
  };
}
