/**
 * Demo Token Storage Utility
 * Manages demo token persistence in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const DEMO_PATIENT_ID_KEY = 'therapybridge_demo_patient_id';
const DEMO_EXPIRES_AT_KEY = 'therapybridge_demo_expires_at';

export const demoTokenStorage = {
  /**
   * Save demo token and metadata to localStorage
   */
  saveToken(token: string, patientId: string, expiresAt: string): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem(DEMO_TOKEN_KEY, token);
      localStorage.setItem(DEMO_PATIENT_ID_KEY, patientId);
      localStorage.setItem(DEMO_EXPIRES_AT_KEY, expiresAt);
      console.log('[Demo] Token saved to localStorage:', { token, patientId });
    } catch (error) {
      console.error('[Demo] Failed to save token:', error);
    }
  },

  /**
   * Get demo token from localStorage
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_TOKEN_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get token:', error);
      return null;
    }
  },

  /**
   * Get demo patient ID from localStorage
   */
  getPatientId(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_PATIENT_ID_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get patient ID:', error);
      return null;
    }
  },

  /**
   * Get demo expiry timestamp from localStorage
   */
  getExpiresAt(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_EXPIRES_AT_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get expiry:', error);
      return null;
    }
  },

  /**
   * Check if demo token is expired
   */
  isExpired(): boolean {
    const expiresAt = this.getExpiresAt();
    if (!expiresAt) return true;

    try {
      const expiry = new Date(expiresAt);
      return expiry < new Date();
    } catch (error) {
      console.error('[Demo] Invalid expiry date:', error);
      return true;
    }
  },

  /**
   * Clear demo token and metadata from localStorage
   */
  clearToken(): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(DEMO_TOKEN_KEY);
      localStorage.removeItem(DEMO_PATIENT_ID_KEY);
      localStorage.removeItem(DEMO_EXPIRES_AT_KEY);
      console.log('[Demo] Token cleared from localStorage');
    } catch (error) {
      console.error('[Demo] Failed to clear token:', error);
    }
  },

  /**
   * Check if demo token exists and is valid
   */
  hasValidToken(): boolean {
    const token = this.getToken();
    return !!token && !this.isExpired();
  },
};
