'use client';

/**
 * Session cards grid component
 * - 4x2 grid (8 cards per page)
 * - Pagination with slide animation
 * - Click card to open fullscreen detail
 * - Supports external session selection (from Timeline sidebar)
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { sessions } from '../lib/mockData';
import { SessionCard } from './SessionCard';
import { SessionDetail } from './SessionDetail';
import { Session } from '../lib/types';

interface SessionCardsGridProps {
  /** Session ID to open in fullscreen (controlled externally, e.g., from Timeline) */
  externalSelectedSessionId?: string | null;
  /** Callback when SessionDetail is closed (to sync external state) */
  onSessionClose?: () => void;
}

export function SessionCardsGrid({
  externalSelectedSessionId,
  onSessionClose
}: SessionCardsGridProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  const cardsPerPage = 8;
  const totalPages = Math.ceil(sessions.length / cardsPerPage);
  const currentSessions = sessions.slice(
    currentPage * cardsPerPage,
    (currentPage + 1) * cardsPerPage
  );

  // Handle external session selection (e.g., from Timeline "View Full Session")
  useEffect(() => {
    if (externalSelectedSessionId) {
      const session = sessions.find(s => s.id === externalSelectedSessionId);
      if (session) {
        setSelectedSession(session);
        // Navigate to the page containing this session
        const sessionIndex = sessions.findIndex(s => s.id === externalSelectedSessionId);
        if (sessionIndex !== -1) {
          setCurrentPage(Math.floor(sessionIndex / cardsPerPage));
        }
      }
    }
  }, [externalSelectedSessionId]);

  // Handle closing the session detail
  const handleClose = useCallback(() => {
    setSelectedSession(null);
    onSessionClose?.();
  }, [onSessionClose]);

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Grid */}
        <motion.div
          key={currentPage}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="grid grid-cols-4 auto-rows-fr gap-4"
        >
          {currentSessions.map((session) => (
            <SessionCard
              key={session.id}
              id={`session-${session.id}`}
              session={session}
              onClick={() => setSelectedSession(session)}
            />
          ))}
        </motion.div>

        {/* Pagination */}
        {totalPages > 1 && (
          <nav aria-label="Session pages" className="flex justify-center items-center gap-2 mt-6">
            {Array.from({ length: totalPages }).map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentPage(idx)}
                aria-label={`Go to page ${idx + 1}`}
                aria-current={idx === currentPage ? 'page' : undefined}
                className={`transition-all rounded-full ${
                  idx === currentPage
                    ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] w-6 h-2'
                    : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 w-2 h-2'
                }`}
              />
            ))}
          </nav>
        )}
      </div>

      {/* Session Detail Fullscreen */}
      {selectedSession && (
        <SessionDetail
          session={selectedSession}
          onClose={handleClose}
        />
      )}
    </>
  );
}
