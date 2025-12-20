'use client';

/**
 * Dashboard sticky header component
 * - Navigation links (Dashboard, Ask AI, Upload)
 * - Home icon + theme toggle (Sun/Moon)
 * - Minimal height design (~60px)
 * - FIXED: Full dark mode support for entire header
 * - Ask AI button triggers fullscreen chat via callback
 */

import { Home, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface HeaderProps {
  onAskAIClick?: () => void;
}

export function Header({ onAskAIClick }: HeaderProps) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-[#1a1625] border-b border-gray-200 dark:border-[#3d3548] h-[60px] flex items-center px-12 transition-colors duration-300">
      <div className="w-full max-w-[1400px] mx-auto flex items-center justify-between">
        {/* Left section - Home icon + Theme toggle */}
        <div className="flex items-center gap-2">
          <button
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
            aria-label="Go to home"
          >
            <Home className="w-5 h-5 text-gray-700 dark:text-gray-200" />
          </button>
          <button
            onClick={toggleTheme}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-amber-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Center section - Navigation */}
        <nav className="flex items-center gap-8">
          <button className="text-sm font-medium text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa] pb-1">
            Dashboard
          </button>
          <button
            onClick={onAskAIClick}
            className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors"
          >
            Ask AI
          </button>
          <button className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">
            Upload
          </button>
        </nav>

        {/* Right section - Empty for balance */}
        <div className="w-[84px]" />
      </div>
    </header>
  );
}
