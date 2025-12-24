/**
 * Demo Token Storage Utility
 * Manages demo token lifecycle in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const PATIENT_ID_KEY = 'therapybridge_patient_id';
const SESSION_IDS_KEY = 'therapybridge_session_ids';
const EXPIRES_AT_KEY = 'therapybridge_demo_expires';
const INIT_STATUS_KEY = 'therapybridge_init_status';

export const demoTokenStorage = {
  /**
   * Store demo credentials after initialization
   */
  store(demoToken: string, patientId: string, sessionIds: string[], expiresAt: string) {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem(DEMO_TOKEN_KEY, demoToken);
      localStorage.setItem(PATIENT_ID_KEY, patientId);
      localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(sessionIds));
      localStorage.setItem(EXPIRES_AT_KEY, expiresAt);
      localStorage.setItem(INIT_STATUS_KEY, 'complete');

      console.log('[Storage] ✓ Demo credentials stored:', { patientId, sessionCount: sessionIds.length });
    } catch (error) {
      console.error('[Storage] ✗ Failed to store credentials:', error);
      throw error; // Propagate error to caller
    }
  },

  /**
   * Retrieve stored demo token (returns null if expired or missing)
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;

    const token = localStorage.getItem(DEMO_TOKEN_KEY);
    const expiresAt = localStorage.getItem(EXPIRES_AT_KEY);

    if (!token || !expiresAt) return null;

    // Check if expired
    const expiry = new Date(expiresAt);
    if (expiry < new Date()) {
      console.log('[Storage] Token expired, clearing...');
      this.clear();
      return null;
    }

    return token;
  },

  /**
   * Get patient ID
   */
  getPatientId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(PATIENT_ID_KEY);
  },

  /**
   * Get session IDs
   */
  getSessionIds(): string[] | null {
    if (typeof window === 'undefined') return null;

    const sessionIdsJson = localStorage.getItem(SESSION_IDS_KEY);
    if (!sessionIdsJson) return null;

    try {
      return JSON.parse(sessionIdsJson);
    } catch {
      return null;
    }
  },

  /**
   * Check if demo is initialized
   */
  isInitialized(): boolean {
    return this.getToken() !== null && this.getPatientId() !== null;
  },

  /**
   * Check initialization status
   * Returns: 'complete' | 'pending' | 'none'
   */
  getInitStatus(): 'complete' | 'pending' | 'none' {
    if (typeof window === 'undefined') return 'none';

    const status = localStorage.getItem(INIT_STATUS_KEY);
    if (status === 'complete') return 'complete';
    if (status === 'pending') return 'pending';
    return 'none';
  },

  /**
   * Mark initialization as pending
   */
  markInitPending() {
    if (typeof window === 'undefined') return;
    localStorage.setItem(INIT_STATUS_KEY, 'pending');
  },

  /**
   * Clear all demo data
   */
  clear() {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(PATIENT_ID_KEY);
    localStorage.removeItem(SESSION_IDS_KEY);
    localStorage.removeItem(EXPIRES_AT_KEY);
    localStorage.removeItem(INIT_STATUS_KEY);

    console.log('[Storage] ✓ All demo data cleared');
  }
};
