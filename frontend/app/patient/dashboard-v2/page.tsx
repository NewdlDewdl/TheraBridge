'use client';

import { Suspense, useState, useEffect } from 'react';

// ============================================================================
// Dashboard V2 Widget Imports
// ============================================================================
import { NotesGoalsPanel } from '@/components/dashboard-v2/NotesGoalsPanel';
import { AIChatWidget } from '@/components/dashboard-v2/AIChatWidget';
import { ToDoCard } from '@/components/dashboard-v2/ToDoCard';
import { ProgressPatternsCard } from '@/components/dashboard-v2/ProgressPatternsCard';
import { TherapistBridgeCard } from '@/components/dashboard-v2/TherapistBridgeCard';
import { SessionCardsGrid } from '@/components/dashboard-v2/SessionCardsGrid';
import TimelineSidebar from '@/components/dashboard-v2/TimelineSidebar';
import { DashboardV2Skeleton } from '@/components/dashboard-v2/skeletons/DashboardV2Skeletons';

// ============================================================================
// Constants
// ============================================================================
const DESKTOP_MIN_WIDTH = 1024;

// ============================================================================
// Dashboard V2 Page Component
// ============================================================================
/**
 * Dashboard V2 - Widget-Based Therapy Progress Dashboard
 *
 * Grid Layout Structure:
 * ┌────────────────────────────────────────────────┐
 * │  TOP ROW (2 large panels - 50/50 split)        │
 * │  ┌──────────────┐  ┌──────────────┐            │
 * │  │ Notes/Goals  │  │ AI Chat      │            │
 * │  │ (50%)        │  │ (50%)        │            │
 * │  └──────────────┘  └──────────────┘            │
 * ├────────────────────────────────────────────────┤
 * │  MIDDLE ROW (3 equal cards - 33/33/33)         │
 * │  ┌─────┐ ┌─────┐ ┌─────┐                       │
 * │  │ToDo │ │Prog.│ │Bridge│                      │
 * │  │(33%)│ │(33%)│ │(33%) │                      │
 * │  └─────┘ └─────┘ └─────┘                       │
 * ├────────────────────────────────────────────────┤
 * │  BOTTOM ROW (80/20 split)                      │
 * │  ┌────────────────────┐ ┌─────────┐            │
 * │  │ Session Cards      │ │Timeline │            │
 * │  │ (80%)              │ │ (20%)   │            │
 * │  └────────────────────┘ └─────────┘            │
 * └────────────────────────────────────────────────┘
 *
 * Spacing:
 * - Gap between cards: 24px (gap-6)
 * - Section spacing: 40px vertical (space-y-10)
 * - Container max-width: 1400px (spec requirement)
 */
export default function DashboardV2Page() {
  const [isDesktop, setIsDesktop] = useState<boolean | null>(null);

  // Desktop-only gate: Check window width on mount and resize
  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(window.innerWidth >= DESKTOP_MIN_WIDTH);
    };

    // Initial check
    checkDesktop();

    // Listen for resize events
    window.addEventListener('resize', checkDesktop);
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  // Show nothing while checking (prevents flash)
  if (isDesktop === null) {
    return null;
  }

  // Mobile/tablet gate: Show message for screens < 1024px
  if (!isDesktop) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Desktop Required
          </h2>
          <p className="text-muted-foreground">
            This dashboard is optimized for desktop viewing. Please use a larger screen.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Main Dashboard Container - 1400px max width per spec */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Suspense boundary with skeleton fallback */}
        <Suspense fallback={<DashboardV2Skeleton />}>
          {/* Dashboard Content - 40px vertical spacing between rows */}
          <div className="space-y-10">

            {/* ============================================================ */}
            {/* TOP ROW - Notes/Goals & AI Chat (50/50 split)               */}
            {/* ============================================================ */}
            <section aria-label="Primary widgets">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Notes/Goals Panel - Left (50%) */}
                <NotesGoalsPanel className="min-h-[280px]" />

                {/* AI Chat Widget - Right (50%) */}
                <AIChatWidget className="min-h-[280px]" />
              </div>
            </section>

            {/* ============================================================ */}
            {/* MIDDLE ROW - ToDo, Progress, Bridge (33/33/33 split)        */}
            {/* ============================================================ */}
            <section aria-label="Action widgets">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* ToDo Card - Left (33%) */}
                <ToDoCard className="min-h-[320px]" />

                {/* Progress Patterns Card - Center (33%) */}
                <ProgressPatternsCard className="min-h-[320px]" />

                {/* Therapist Bridge Card - Right (33%) */}
                <TherapistBridgeCard className="min-h-[320px]" />
              </div>
            </section>

            {/* ============================================================ */}
            {/* BOTTOM ROW - Session Cards & Timeline (80/20 split)         */}
            {/* ============================================================ */}
            <section aria-label="Session history">
              <div className="grid grid-cols-1 md:grid-cols-[4fr_1fr] gap-6">
                {/* Session Cards Grid - Left (80%) */}
                <SessionCardsGrid className="min-h-[400px]" />

                {/* Timeline Sidebar - Right (20%) */}
                <TimelineSidebar className="min-h-[400px] sticky top-8" />
              </div>
            </section>

          </div>
        </Suspense>
      </div>
    </div>
  );
}
