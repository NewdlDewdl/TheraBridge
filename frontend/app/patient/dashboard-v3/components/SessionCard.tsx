'use client';

/**
 * Individual session card component
 * - Two-column layout with implicit hierarchy
 * - Mood-based left border accent
 * - Milestone badge (if applicable)
 * - FIXED: Dark mode support
 */

import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import { Session } from '../lib/types';
import { getMoodColor, getMoodEmoji } from '../lib/utils';

interface SessionCardProps {
  session: Session;
  onClick: () => void;
}

export function SessionCard({ session, onClick }: SessionCardProps) {
  const moodColor = getMoodColor(session.mood);
  const moodEmoji = getMoodEmoji(session.mood);

  return (
    <motion.div
      onClick={onClick}
      className="relative bg-gradient-to-br from-white to-[#FEFDFB] dark:from-[#2a2435] dark:to-[#1a1625] rounded-xl p-5 cursor-pointer overflow-visible flex flex-col min-h-[280px] transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
      style={{
        borderLeft: `3px solid ${moodColor}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
      }}
      whileHover={{
        y: -4,
        boxShadow: '0 6px 16px rgba(0,0,0,0.12)'
      }}
      transition={{ duration: 0.2 }}
      role="button"
      tabIndex={0}
      aria-label={`Session on ${session.date}, mood ${session.mood}, topics ${session.topics.join(', ')}, strategy ${session.strategy}${session.milestone ? ', breakthrough session' : ''}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Milestone Badge */}
      {session.milestone && (
        <div
          className="absolute -top-2.5 left-4 px-3 py-1 bg-[#FEF3C7] rounded-full flex items-center gap-1.5 z-10"
          style={{
            boxShadow: '0 0 12px rgba(251,191,36,0.4)'
          }}
        >
          <Star className="w-3 h-3 text-[#92400E] fill-[#92400E]" />
          <span className="text-[10px] uppercase font-medium text-[#92400E] tracking-wide">
            {session.milestone.title.split(':')[0]}
          </span>
        </div>
      )}

      {/* Metadata Row */}
      <div className="flex items-center justify-center gap-2.5 mb-5 flex-shrink-0">
        <span className="text-sm font-mono uppercase text-gray-500 dark:text-gray-500">{session.duration}</span>
        <span className="text-gray-400 dark:text-gray-600">•</span>
        <span className="text-lg font-bold text-gray-800 dark:text-gray-200">{session.date}</span>
        <span className="text-gray-400 dark:text-gray-600">•</span>
        <span className="text-xl">{moodEmoji}</span>
      </div>

      {/* Two-column Layout */}
      <div className="flex-1 flex flex-col">
        {/* Upper 2/3: Two columns with separator */}
        <div className="grid grid-cols-2 gap-5 relative flex-[2] pt-3">
          {/* Vertical Separator Line */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200 dark:bg-[#3d3548] opacity-50 -translate-x-1/2" />

          {/* Left Column - Topics */}
          <div className="pr-3">
            <ul className="space-y-2.5">
              {session.topics.map((topic, idx) => (
                <li key={idx} className="text-[15px] font-[350] text-gray-700 dark:text-gray-300 leading-relaxed">
                  {topic}
                </li>
              ))}
            </ul>
          </div>

          {/* Right Column - Strategy */}
          <div className="pl-3">
            <p className="text-[15px] font-semibold text-[#5AB9B4] dark:text-[#a78bfa] leading-relaxed">
              {session.strategy}
            </p>
          </div>
        </div>

        {/* Bottom 1/3: Action items full width */}
        {session.actions.length > 0 && (
          <div className="flex-1 pt-4 border-t border-gray-100 dark:border-[#3d3548] mt-4">
            <ul className="space-y-2">
              {session.actions.map((action, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-[14px] font-[350] text-gray-600 dark:text-gray-400 leading-relaxed">
                  <span className="text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5 flex-shrink-0 font-semibold">•</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  );
}
