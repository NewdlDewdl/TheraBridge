'use client';

/**
 * Timeline sidebar component
 * - Vertical gradient connector line
 * - Colored dots for mood (star icons for milestones)
 * - Click to show popover with session preview
 * - Enhanced popover matching PAGE_LAYOUT_ARCHITECTURE.md spec
 * - Keyboard accessible (Escape to close)
 * - Click outside to close
 * - FIXED: Dark mode support
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Clock, ArrowRight } from 'lucide-react';
import { timelineData } from '../lib/mockData';
import { TimelineEntry } from '../lib/types';
import { getMoodColor, popoverVariants } from '../lib/utils';

interface TimelineSidebarProps {
  /** Callback when "View Full Session" is clicked - receives sessionId */
  onViewSession?: (sessionId: string) => void;
  /** Callback when timeline entry is clicked - scrolls to session card */
  onScrollToSession?: (sessionId: string) => void;
}

export function TimelineSidebar({ onViewSession, onScrollToSession }: TimelineSidebarProps) {
  const [selectedEntry, setSelectedEntry] = useState<TimelineEntry | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleEntryClick = (entry: TimelineEntry) => {
    // Toggle popover visibility
    const isClosing = selectedEntry?.sessionId === entry.sessionId;
    setSelectedEntry(isClosing ? null : entry);

    // Scroll to card when opening (not when closing)
    if (!isClosing && onScrollToSession) {
      onScrollToSession(entry.sessionId);
    }
  };

  const handleViewSession = useCallback((sessionId: string) => {
    if (onViewSession) {
      onViewSession(sessionId);
    }
    setSelectedEntry(null);
  }, [onViewSession]);

  // Keyboard accessibility - close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedEntry) {
        setSelectedEntry(null);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [selectedEntry]);

  // Click outside to close popover
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setSelectedEntry(null);
      }
    };
    if (selectedEntry) {
      // Delay to prevent immediate close on the click that opened it
      const timer = setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside);
      }, 0);
      return () => {
        clearTimeout(timer);
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [selectedEntry]);

  // Format duration for display (e.g., "50m" -> "50 minutes")
  const formatDuration = (duration: string): string => {
    const match = duration.match(/(\d+)m?/);
    if (match) {
      const mins = parseInt(match[1], 10);
      return `${mins} minutes`;
    }
    return duration;
  };

  return (
    <div
      ref={containerRef}
      className="bg-white dark:bg-[#2a2435] rounded-xl border border-gray-200 dark:border-[#3d3548] p-4 h-full overflow-y-auto relative transition-colors duration-300"
    >
      <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200 mb-6">Timeline</h3>

      {/* Timeline Entries */}
      <div className="relative">
        {/* Gradient Connector Line */}
        <div
          className="absolute left-[7px] top-0 bottom-0 w-[2px]"
          style={{
            background: 'linear-gradient(180deg, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%)'
          }}
        />

        {/* Entries */}
        <div className="space-y-6 relative">
          {timelineData.map((entry) => {
            const moodColor = getMoodColor(entry.mood);
            const isMilestone = !!entry.milestone;
            const isSelected = selectedEntry?.sessionId === entry.sessionId;

            return (
              <div key={entry.sessionId} className="relative">
                <button
                  onClick={() => handleEntryClick(entry)}
                  aria-expanded={isSelected}
                  aria-haspopup="dialog"
                  className={`flex items-start gap-4 w-full text-left rounded-lg p-2 -ml-2 transition-all duration-200
                    ${isSelected
                      ? 'bg-gray-100 dark:bg-[#3d3548] ring-2 ring-[#5AB9B4]/50 dark:ring-[#a78bfa]/50'
                      : 'hover:bg-gray-50 dark:hover:bg-[#3d3548]/50'
                    }`}
                >
                  {/* Timeline Dot/Icon */}
                  <div className="relative flex-shrink-0">
                    {isMilestone ? (
                      <Star
                        className="w-[14px] h-[14px] text-amber-600 fill-amber-600 relative z-10"
                        style={{
                          filter: 'drop-shadow(0 0 4px rgba(251,191,36,0.4))'
                        }}
                      />
                    ) : (
                      <div
                        className={`w-[10px] h-[10px] rounded-full relative z-10 transition-transform duration-200 ${
                          isSelected ? 'scale-125' : 'hover:scale-110'
                        }`}
                        style={{ backgroundColor: moodColor }}
                      />
                    )}
                  </div>

                  {/* Entry Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium text-gray-800 dark:text-gray-200">{entry.date}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">{entry.topic}</p>
                    {isMilestone && (
                      <p className="text-[11px] italic text-amber-700 dark:text-amber-500 mt-0.5">
                        {entry.milestone?.title.split(':')[0]}
                      </p>
                    )}
                  </div>
                </button>

                {/* Enhanced Popover */}
                <AnimatePresence>
                  {isSelected && (
                    <motion.div
                      ref={popoverRef}
                      variants={popoverVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      role="dialog"
                      aria-label={`Session ${entry.sessionId.replace('s', '')} details`}
                      tabIndex={-1}
                      className="absolute left-full ml-3 top-0 w-[300px] bg-white dark:bg-[#2a2435] rounded-xl shadow-2xl p-5 z-50 border-2 border-gray-200 dark:border-[#4a4258]"
                    >
                      {/* Arrow pointing to timeline entry */}
                      <div className="absolute right-full top-4">
                        <div className="w-0 h-0 border-t-[8px] border-b-[8px] border-r-[10px] border-transparent border-r-gray-200 dark:border-r-[#4a4258]" />
                        <div className="absolute top-[-6px] left-[2px] w-0 h-0 border-t-[6px] border-b-[6px] border-r-[8px] border-transparent border-r-white dark:border-r-[#2a2435]" />
                      </div>

                      {/* Header: Session number + date */}
                      <h4 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-4">
                        Session {entry.sessionId.replace('s', '')} - {entry.date}
                      </h4>

                      {/* Duration & Mood Row */}
                      <div className="flex items-center gap-6 mb-4 pb-4 border-b border-gray-100 dark:border-[#3d3548]">
                        {/* Duration */}
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {formatDuration(entry.duration)}
                          </span>
                        </div>

                        {/* Mood */}
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: moodColor }}
                          />
                          <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                            {entry.mood}
                          </span>
                        </div>
                      </div>

                      {/* Topics Section */}
                      <div className="mb-4">
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-500 uppercase tracking-wide mb-2">
                          Topics
                        </p>
                        <ul className="space-y-1">
                          {entry.topic.split(', ').map((topic, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-gray-400 dark:text-gray-500 mt-0.5">•</span>
                              <span className="text-sm text-gray-700 dark:text-gray-300">{topic}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Strategy Section */}
                      <div className="mb-4 pb-4 border-b border-gray-100 dark:border-[#3d3548]">
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-500 uppercase tracking-wide mb-2">
                          Strategy
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{entry.strategy}</p>
                      </div>

                      {/* Milestone/Breakthrough Section (conditional) */}
                      {entry.milestone && (
                        <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/40">
                          <div className="flex items-center gap-2 mb-2">
                            <Star className="w-4 h-4 text-amber-600 fill-amber-500" />
                            <span className="text-sm font-medium text-amber-800 dark:text-amber-400">
                              {entry.milestone.title.includes(':')
                                ? entry.milestone.title.split(':')[0]
                                : 'Milestone'}
                            </span>
                          </div>
                          <p className="text-sm text-amber-700 dark:text-amber-300/80 leading-relaxed">
                            {entry.milestone.title.includes(':')
                              ? entry.milestone.title.split(':')[1].trim()
                              : entry.milestone.description}
                          </p>
                        </div>
                      )}

                      {/* View Full Session Button */}
                      <button
                        onClick={() => handleViewSession(entry.sessionId)}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4
                          bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/15
                          hover:bg-[#5AB9B4]/20 dark:hover:bg-[#a78bfa]/25
                          text-[#4a9e9a] dark:text-[#a78bfa]
                          rounded-lg transition-colors duration-200
                          text-sm font-medium"
                      >
                        View Full Session
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
