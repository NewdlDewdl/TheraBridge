'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, TrendingDown, TrendingUp, Minus, CheckCircle2, Circle } from 'lucide-react';

/**
 * MOCKUP 1: "Serene Analytics"
 *
 * Design Philosophy:
 * - Refined minimalism with generous spacing
 * - Soft gradients and ethereal backgrounds
 * - Clinical data presented with warmth
 * - Typography: Editorial serif for headings, clean sans for data
 *
 * Color Palette (therapy-appropriate):
 * - Primary: Soft teal (#5AB9B4) - calming, trust, growth
 * - Secondary: Warm lavender (#B8A5D6) - comfort, healing
 * - Accent: Gentle coral (#F4A69D) - warmth, encouragement
 * - Neutral: Warm gray (#F7F5F3) - safety, softness
 */

export default function DashboardMockupSerene() {
  // Mock clinical screening data
  const phq9Data = [
    { session: 1, score: 18, date: '2025-10-15' },
    { session: 2, score: 16, date: '2025-10-22' },
    { session: 3, score: 15, date: '2025-10-29' },
    { session: 4, score: 13, date: '2025-11-05' },
    { session: 5, score: 12, date: '2025-11-12' },
    { session: 6, score: 11, date: '2025-11-19' },
    { session: 7, score: 9, date: '2025-11-26' },
    { session: 8, score: 8, date: '2025-12-03' },
    { session: 9, score: 7, date: '2025-12-10' },
    { session: 10, score: 6, date: '2025-12-17' },
  ];

  const gad7Data = [
    { session: 1, score: 15, date: '2025-10-15' },
    { session: 2, score: 14, date: '2025-10-22' },
    { session: 3, score: 13, date: '2025-10-29' },
    { session: 4, score: 12, date: '2025-11-05' },
    { session: 5, score: 10, date: '2025-11-12' },
    { session: 6, score: 9, date: '2025-11-19' },
    { session: 7, score: 8, date: '2025-11-26' },
    { session: 8, score: 7, date: '2025-12-03' },
    { session: 9, score: 6, date: '2025-12-10' },
    { session: 10, score: 5, date: '2025-12-17' },
  ];

  const sessions = [
    {
      id: 10,
      date: 'Dec 17, 2025',
      duration: '50 min',
      mood: 'positive',
      topics: 'Relationship boundaries, self-advocacy',
      strategy: 'Assertiveness training',
      actions: ['Set boundary with friend', 'Journal wins'],
    },
    {
      id: 9,
      date: 'Dec 10, 2025',
      duration: '45 min',
      mood: 'positive',
      topics: 'Self-worth, past relationships',
      strategy: 'Laddering technique',
      actions: ['Self-compassion practice', 'Behavioral experiment'],
      milestone: 'Breakthrough: self-compassion',
    },
    {
      id: 8,
      date: 'Dec 3, 2025',
      duration: '48 min',
      mood: 'neutral',
      topics: 'Work stress, anxiety triggers',
      strategy: '4-7-8 breathing',
      actions: ['Practice breathing 2x daily', 'Track anxiety'],
    },
    {
      id: 7,
      date: 'Nov 26, 2025',
      duration: '45 min',
      mood: 'neutral',
      topics: 'Family dynamics, holiday stress',
      strategy: 'Grounding techniques',
      actions: ['5-4-3-2-1 during stress', 'Set boundaries'],
      milestone: 'New strategy: Grounding',
    },
    {
      id: 6,
      date: 'Nov 19, 2025',
      duration: '50 min',
      mood: 'low',
      topics: 'Loneliness, social isolation',
      strategy: 'Behavioral activation',
      actions: ['Attend social event', 'Call friend weekly'],
    },
    {
      id: 5,
      date: 'Nov 12, 2025',
      duration: '45 min',
      mood: 'neutral',
      topics: 'Sleep issues, rumination',
      strategy: 'Sleep hygiene plan',
      actions: ['No screens 1hr before bed', 'Journaling'],
      milestone: 'PHQ-9 score improved 30%',
    },
  ];

  const activeHomework = [
    { text: 'Set boundary with friend about time commitments', completed: false, sessionId: 10 },
    { text: 'Journal daily wins and moments of self-advocacy', completed: false, sessionId: 10 },
    { text: 'Practice self-compassion when negative thoughts arise', completed: true, sessionId: 9 },
    { text: 'Conduct behavioral experiment with trusted friend', completed: false, sessionId: 9 },
    { text: 'Use 4-7-8 breathing when feeling anxious (2x daily)', completed: true, sessionId: 8 },
    { text: 'Track anxiety triggers in journal', completed: true, sessionId: 8 },
  ];

  const completionRate = Math.round(
    (activeHomework.filter((h) => h.completed).length / activeHomework.length) * 100
  );

  // Calculate PHQ-9 and GAD-7 trends
  const phq9Current = phq9Data[phq9Data.length - 1].score;
  const phq9Previous = phq9Data[0].score;
  const phq9Change = phq9Previous - phq9Current;
  const phq9PercentChange = Math.round((phq9Change / phq9Previous) * 100);

  const gad7Current = gad7Data[gad7Data.length - 1].score;
  const gad7Previous = gad7Data[0].score;
  const gad7Change = gad7Previous - gad7Current;
  const gad7PercentChange = Math.round((gad7Change / gad7Previous) * 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 via-teal-50/30 to-purple-50/20">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400;500;600&display=swap');

        .mockup-serene {
          font-family: 'Inter', sans-serif;
        }

        .mockup-serene h1,
        .mockup-serene h2,
        .mockup-serene h3 {
          font-family: 'Crimson Pro', serif;
        }

        .card-hover {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .card-hover:hover {
          transform: translateY(-2px);
          box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.08), 0 8px 10px -6px rgb(0 0 0 / 0.08);
        }

        .timeline-dot {
          animation: pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes pulse-subtle {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        .progress-bar {
          background: linear-gradient(90deg, #5AB9B4 0%, #B8A5D6 100%);
          animation: shimmer 3s ease-in-out infinite;
          background-size: 200% 100%;
        }

        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>

      <div className="mockup-serene max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-semibold text-gray-900 mb-3">Your Journey</h1>
          <p className="text-lg text-gray-600">Tracking progress across 10 sessions</p>
        </div>

        {/* Top Section: Clinical Progress + Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Clinical Screening Trends - Takes 2 columns */}
          <Card className="lg:col-span-2 border-0 shadow-lg bg-white/80 backdrop-blur card-hover">
            <CardHeader>
              <CardTitle className="text-2xl">Clinical Progress</CardTitle>
              <p className="text-sm text-gray-500">Standardized mental health screenings</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-8">
                {/* PHQ-9 Depression */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                        Depression (PHQ-9)
                      </h4>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-4xl font-semibold text-teal-600">{phq9Current}</span>
                        <span className="text-sm text-gray-400">/ 27</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-green-600">
                        <TrendingDown className="w-5 h-5" />
                        <span className="text-xl font-semibold">{phq9PercentChange}%</span>
                      </div>
                      <span className="text-xs text-gray-500">improvement</span>
                    </div>
                  </div>
                  {/* Mini line chart */}
                  <div className="relative h-24 flex items-end gap-1">
                    {phq9Data.map((point, idx) => {
                      const height = (point.score / 27) * 100;
                      return (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-teal-400 to-teal-300 rounded-t transition-all hover:from-teal-500 hover:to-teal-400"
                          style={{ height: `${height}%` }}
                          title={`Session ${point.session}: ${point.score}`}
                        />
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>Session 1</span>
                    <span>Session 10</span>
                  </div>
                </div>

                {/* GAD-7 Anxiety */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                        Anxiety (GAD-7)
                      </h4>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className="text-4xl font-semibold text-purple-600">{gad7Current}</span>
                        <span className="text-sm text-gray-400">/ 21</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-green-600">
                        <TrendingDown className="w-5 h-5" />
                        <span className="text-xl font-semibold">{gad7PercentChange}%</span>
                      </div>
                      <span className="text-xs text-gray-500">improvement</span>
                    </div>
                  </div>
                  {/* Mini line chart */}
                  <div className="relative h-24 flex items-end gap-1">
                    {gad7Data.map((point, idx) => {
                      const height = (point.score / 21) * 100;
                      return (
                        <div
                          key={idx}
                          className="flex-1 bg-gradient-to-t from-purple-400 to-purple-300 rounded-t transition-all hover:from-purple-500 hover:to-purple-400"
                          style={{ height: `${height}%` }}
                          title={`Session ${point.session}: ${point.score}`}
                        />
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>Session 1</span>
                    <span>Session 10</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Homework Completion */}
          <Card className="border-0 shadow-lg bg-gradient-to-br from-teal-500 to-teal-600 text-white card-hover">
            <CardHeader>
              <CardTitle className="text-white/90 text-sm uppercase tracking-wide font-medium">
                Homework Completion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-6xl font-bold mb-4">{completionRate}%</div>
              <div className="w-full bg-white/20 rounded-full h-3 mb-4 overflow-hidden">
                <div
                  className="progress-bar h-full rounded-full"
                  style={{ width: `${completionRate}%` }}
                />
              </div>
              <p className="text-sm text-white/80">
                {activeHomework.filter((h) => h.completed).length} of {activeHomework.length} tasks
                completed
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Middle Section: Timeline */}
        <Card className="mb-8 border-0 shadow-lg bg-white/80 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-2xl">Session Timeline</CardTitle>
            <p className="text-sm text-gray-500">Your therapy journey with key milestones</p>
          </CardHeader>
          <CardContent>
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-teal-200 via-purple-200 to-teal-200" />

              <div className="space-y-6">
                {sessions.map((session, idx) => (
                  <div key={session.id} className="relative pl-16">
                    {/* Timeline dot */}
                    <div
                      className={`absolute left-3.5 w-5 h-5 rounded-full border-4 border-white ${
                        session.milestone
                          ? 'bg-amber-400 timeline-dot shadow-lg shadow-amber-400/50'
                          : session.mood === 'positive'
                          ? 'bg-teal-400'
                          : session.mood === 'neutral'
                          ? 'bg-purple-300'
                          : 'bg-rose-300'
                      }`}
                    />

                    {/* Session content */}
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-semibold text-gray-900">{session.date}</span>
                          <span className="text-sm text-gray-500">{session.duration}</span>
                          {session.milestone && (
                            <Badge className="bg-amber-100 text-amber-800 border-amber-200">
                              ⭐ {session.milestone}
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <div>{session.topics}</div>
                          <div className="text-teal-600 font-medium">{session.strategy}</div>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {session.actions.slice(0, 2).map((action, i) => (
                              <span
                                key={i}
                                className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                              >
                                {action}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bottom Section: Active Homework */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-2xl">Active Homework</CardTitle>
            <p className="text-sm text-gray-500">Tasks to practice between sessions</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeHomework.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {item.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-teal-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-300 flex-shrink-0 mt-0.5" />
                  )}
                  <span
                    className={`flex-1 ${
                      item.completed ? 'text-gray-400 line-through' : 'text-gray-700'
                    }`}
                  >
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
