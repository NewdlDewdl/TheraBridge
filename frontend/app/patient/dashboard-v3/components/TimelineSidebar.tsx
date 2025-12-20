'use client';

/**
 * Timeline sidebar component
 * - Vertical gradient connector line
 * - Colored dots for mood (star icons for milestones)
 * - Click to show popover with session preview
 * - FIXED: Dark mode support
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star } from 'lucide-react';
import { timelineData } from '../lib/mockData';
import { TimelineEntry } from '../lib/types';
import { getMoodColor, popoverVariants } from '../lib/utils';

export function TimelineSidebar() {
  const [selectedEntry, setSelectedEntry] = useState<TimelineEntry | null>(null);

  const handleEntryClick = (entry: TimelineEntry) => {
    setSelectedEntry(selectedEntry?.sessionId === entry.sessionId ? null : entry);
  };

  return (
    <div className="bg-white dark:bg-[#2a2435] rounded-xl border border-gray-200 dark:border-[#3d3548] p-4 h-full overflow-y-auto relative transition-colors duration-300">
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

            return (
              <div key={entry.sessionId} className="relative">
                <button
                  onClick={() => handleEntryClick(entry)}
                  className="flex items-start gap-4 w-full text-left hover:bg-gray-50 dark:hover:bg-[#3d3548] rounded-lg p-2 -ml-2 transition-colors"
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
                        className="w-[10px] h-[10px] rounded-full relative z-10"
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

                {/* Popover */}
                <AnimatePresence>
                  {selectedEntry?.sessionId === entry.sessionId && (
                    <motion.div
                      variants={popoverVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      className="absolute left-full ml-3 top-0 w-[300px] bg-white dark:bg-[#2a2435] rounded-xl shadow-xl p-4 z-50 border-2 border-gray-300 dark:border-gray-600"
                    >
                      {/* Arrow */}
                      <div
                        className="absolute right-full top-4 w-0 h-0 border-t-[6px] border-b-[6px] border-r-[8px] border-transparent border-r-gray-300 dark:border-r-gray-600"
                      />

                      {/* Content */}
                      <div className="mb-3">
                        <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-1">
                          Session {entry.sessionId.replace('s', '')} - {entry.date}
                        </h4>
                        {entry.milestone && (
                          <div className="flex items-center gap-2 mb-2">
                            <Star className="w-3 h-3 text-amber-600 fill-amber-600" />
                            <span className="text-xs text-amber-900 dark:text-amber-400 font-medium">
                              {entry.milestone.title}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="space-y-3 text-sm">
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mb-1">Topics</p>
                          <p className="text-gray-700 dark:text-gray-300">{entry.topic}</p>
                        </div>

                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mb-1">Mood</p>
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: moodColor }}
                            />
                            <span className="text-gray-700 dark:text-gray-300 capitalize">{entry.mood}</span>
                          </div>
                        </div>

                        {entry.milestone && (
                          <div className="pt-2 border-t border-gray-200 dark:border-[#3d3548]">
                            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                              {entry.milestone.description}
                            </p>
                          </div>
                        )}
                      </div>

                      <button
                        onClick={() => setSelectedEntry(null)}
                        className="mt-3 text-xs text-[#5AB9B4] dark:text-[#a78bfa] hover:opacity-80 font-medium"
                      >
                        View Full Session →
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
