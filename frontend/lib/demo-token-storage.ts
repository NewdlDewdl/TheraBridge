/**
 * Demo Token Storage Utility
 * Manages demo token lifecycle in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const PATIENT_ID_KEY = 'therapybridge_patient_id';
const SESSION_IDS_KEY = 'therapybridge_session_ids';
const EXPIRES_AT_KEY = 'therapybridge_demo_expires';

export const demoTokenStorage = {
  /**
   * Store demo credentials after initialization
   */
  store(demoToken: string, patientId: string, sessionIds: string[], expiresAt: string) {
    if (typeof window === 'undefined') return;

    localStorage.setItem(DEMO_TOKEN_KEY, demoToken);
    localStorage.setItem(PATIENT_ID_KEY, patientId);
    localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(sessionIds));
    localStorage.setItem(EXPIRES_AT_KEY, expiresAt);
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
   * Clear all demo data
   */
  clear() {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(PATIENT_ID_KEY);
    localStorage.removeItem(SESSION_IDS_KEY);
    localStorage.removeItem(EXPIRES_AT_KEY);
  }
};
