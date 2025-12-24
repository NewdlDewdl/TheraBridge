'use client';

/**
 * ThemeContext - Bridge to next-themes
 * This file now acts as a compatibility layer between the old patient theme context
 * and the new next-themes implementation in the root layout.
 *
 * All components using this context will automatically work with next-themes.
 */

import { ReactNode } from 'react';
import { useTheme as useNextTheme } from 'next-themes';

interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
}

/**
 * ThemeProvider - Now a compatibility wrapper
 * NOTE: This is no longer needed in pages since ThemeProvider is in the root layout.
 * This export exists only for backwards compatibility with existing code.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  // Just pass through - the real provider is in the root layout
  return <>{children}</>;
}

/**
 * useTheme hook - Bridges to next-themes
 */
export function useTheme(): ThemeContextType {
  const { theme, setTheme } = useNextTheme();

  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');

  return {
    isDark,
    toggleTheme,
  };
}
