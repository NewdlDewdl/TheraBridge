'use client';

/**
 * TherapyBridge Dashboard - Main application entry
 * - Full dashboard layout with 7 interactive components
 * - Grid-based responsive layout
 * - Warm cream background with therapy-appropriate aesthetics
 * - FIXED: Full dark mode support across entire page
 */

import { ThemeProvider } from './contexts/ThemeContext';
import { Header } from './components/Header';
import { NotesGoalsCard } from './components/NotesGoalsCard';
import { AIChatCard } from './components/AIChatCard';
import { ToDoCard } from './components/ToDoCard';
import { ProgressPatternsCard } from './components/ProgressPatternsCard';
import { TherapistBridgeCard } from './components/TherapistBridgeCard';
import { SessionCardsGrid } from './components/SessionCardsGrid';
import { TimelineSidebar } from './components/TimelineSidebar';

export default function DashboardV3Page() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-[#F7F5F3] dark:bg-[#1a1625] transition-colors duration-300">
        {/* Header */}
        <Header />

        {/* Main Container */}
        <main className="w-full max-w-[1400px] mx-auto px-12 py-12">
          {/* Top Row - 50/50 Split */}
          <div className="grid grid-cols-2 gap-6 mb-10">
            <NotesGoalsCard />
            <AIChatCard />
          </div>

          {/* Middle Row - 3 Equal Cards */}
          <div className="grid grid-cols-3 gap-6 mb-10">
            <ToDoCard />
            <ProgressPatternsCard />
            <TherapistBridgeCard />
          </div>

          {/* Bottom Row - 80/20 Split */}
          <div className="grid grid-cols-[1fr_250px] gap-6">
            <div className="min-h-[650px]">
              <SessionCardsGrid />
            </div>
            <div className="h-[650px] sticky top-[84px]">
              <TimelineSidebar />
            </div>
          </div>
        </main>
      </div>
    </ThemeProvider>
  );
}
