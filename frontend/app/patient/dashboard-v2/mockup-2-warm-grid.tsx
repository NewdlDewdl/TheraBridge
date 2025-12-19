'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingDown, CheckCircle2, Circle, Sparkles } from 'lucide-react';

/**
 * MOCKUP 2: "Warm Grid"
 *
 * Design Philosophy:
 * - Masonry-style grid with organic card sizes
 * - Warmer, more approachable color palette
 * - Compact but friendly spacing
 * - Typography: Rounded sans for warmth, geometric for data
 *
 * Color Palette (therapy-appropriate):
 * - Primary: Warm peach (#FFB499) - comfort, warmth
 * - Secondary: Sage green (#A8C69F) - healing, growth
 * - Accent: Soft blue (#8FB8DE) - calm, trust
 * - Neutral: Cream (#FAF8F5) - warmth, safety
 */

export default function DashboardMockupWarmGrid() {
  // Mock data (same as mockup 1)
  const phq9Data = [
    { session: 1, score: 18 },
    { session: 2, score: 16 },
    { session: 3, score: 15 },
    { session: 4, score: 13 },
    { session: 5, score: 12 },
    { session: 6, score: 11 },
    { session: 7, score: 9 },
    { session: 8, score: 8 },
    { session: 9, score: 7 },
    { session: 10, score: 6 },
  ];

  const gad7Data = [
    { session: 1, score: 15 },
    { session: 2, score: 14 },
    { session: 3, score: 13 },
    { session: 4, score: 12 },
    { session: 5, score: 10 },
    { session: 6, score: 9 },
    { session: 7, score: 8 },
    { session: 8, score: 7 },
    { session: 9, score: 6 },
    { session: 10, score: 5 },
  ];

  const sessions = [
    {
      id: 10,
      date: 'Dec 17',
      duration: '50m',
      mood: 'positive',
      topics: 'Relationship boundaries, self-advocacy',
      strategy: 'Assertiveness training',
      actions: ['Set boundary with friend', 'Journal wins'],
    },
    {
      id: 9,
      date: 'Dec 10',
      duration: '45m',
      mood: 'positive',
      topics: 'Self-worth, past relationships',
      strategy: 'Laddering technique',
      actions: ['Self-compassion practice', 'Behavioral experiment'],
      milestone: 'Breakthrough: self-compassion',
    },
    {
      id: 8,
      date: 'Dec 3',
      duration: '48m',
      mood: 'neutral',
      topics: 'Work stress, anxiety triggers',
      strategy: '4-7-8 breathing',
      actions: ['Practice breathing 2x daily', 'Track anxiety'],
    },
    {
      id: 7,
      date: 'Nov 26',
      duration: '45m',
      mood: 'neutral',
      topics: 'Family dynamics, holiday stress',
      strategy: 'Grounding techniques',
      actions: ['5-4-3-2-1 during stress', 'Set boundaries'],
      milestone: 'New strategy: Grounding',
    },
    {
      id: 6,
      date: 'Nov 19',
      duration: '50m',
      mood: 'low',
      topics: 'Loneliness, social isolation',
      strategy: 'Behavioral activation',
      actions: ['Attend social event', 'Call friend weekly'],
    },
    {
      id: 5,
      date: 'Nov 12',
      duration: '45m',
      mood: 'neutral',
      topics: 'Sleep issues, rumination',
      strategy: 'Sleep hygiene plan',
      actions: ['No screens 1hr before bed', 'Journaling'],
      milestone: 'PHQ-9 improved 30%',
    },
    {
      id: 4,
      date: 'Nov 5',
      duration: '50m',
      mood: 'low',
      topics: 'Breakup processing, grief',
      strategy: 'Emotional validation',
      actions: ['Allow feelings without judgment', 'Support group'],
    },
    {
      id: 3,
      date: 'Oct 29',
      duration: '45m',
      mood: 'low',
      topics: 'Core beliefs exploration',
      strategy: 'CBT thought records',
      actions: ['Track negative thoughts', 'Challenge beliefs'],
    },
    {
      id: 2,
      date: 'Oct 22',
      duration: '50m',
      mood: 'neutral',
      topics: 'Therapy goals, treatment plan',
      strategy: 'Goal setting framework',
      actions: ['Define 3 goals', 'Track progress weekly'],
      milestone: 'Treatment plan established',
    },
    {
      id: 1,
      date: 'Oct 15',
      duration: '60m',
      mood: 'neutral',
      topics: 'Initial intake, history',
      strategy: 'Assessment',
      actions: ['Complete intake forms', 'PHQ-9/GAD-7 baseline'],
      milestone: 'First session',
    },
  ];

  const activeHomework = [
    { text: 'Set boundary with friend', completed: false },
    { text: 'Journal daily wins', completed: false },
    { text: 'Self-compassion practice', completed: true },
    { text: 'Behavioral experiment', completed: false },
    { text: '4-7-8 breathing 2x daily', completed: true },
    { text: 'Track anxiety triggers', completed: true },
  ];

  const completionRate = Math.round(
    (activeHomework.filter((h) => h.completed).length / activeHomework.length) * 100
  );

  const phq9Current = phq9Data[phq9Data.length - 1].score;
  const phq9Previous = phq9Data[0].score;
  const phq9Change = phq9Previous - phq9Current;
  const phq9PercentChange = Math.round((phq9Change / phq9Previous) * 100);

  const gad7Current = gad7Data[gad7Data.length - 1].score;
  const gad7Previous = gad7Data[0].score;
  const gad7Change = gad7Previous - gad7Current;
  const gad7PercentChange = Math.round((gad7Change / gad7Previous) * 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50/40 to-rose-50/30">
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap');

        .mockup-warm {
          font-family: 'DM Sans', sans-serif;
        }

        .mockup-warm .mono {
          font-family: 'Space Mono', monospace;
        }

        .card-warm {
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          border-radius: 16px;
        }

        .card-warm:hover {
          transform: scale(1.02);
          box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.15);
        }

        .session-card-warm {
          cursor: pointer;
          position: relative;
          overflow: hidden;
        }

        .session-card-warm::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, #FFB499 0%, #A8C69F 100%);
          transform: scaleX(0);
          transform-origin: left;
          transition: transform 0.3s ease;
        }

        .session-card-warm:hover::before {
          transform: scaleX(1);
        }

        .gradient-text {
          background: linear-gradient(135deg, #FFB499 0%, #FF8A65 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .shimmer {
          animation: shimmer 2s ease-in-out infinite;
        }

        @keyframes shimmer {
          0% {
            opacity: 0.5;
          }
          50% {
            opacity: 1;
          }
          100% {
            opacity: 0.5;
          }
        }
      `}</style>

      <div className="mockup-warm max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold gradient-text mb-2">Progress Dashboard</h1>
          <p className="text-gray-600">10 sessions • Last session: Dec 17, 2025</p>
        </div>

        {/* Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* PHQ-9 Score - Spans 2 columns on large screens */}
          <Card className="lg:col-span-2 bg-gradient-to-br from-orange-100 to-orange-50 border-0 shadow-md card-warm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold text-gray-700">
                    Depression (PHQ-9)
                  </CardTitle>
                  <p className="text-xs text-gray-500 mt-1">0-27 scale</p>
                </div>
                <div className="flex items-center gap-1 text-green-600">
                  <TrendingDown className="w-4 h-4" />
                  <span className="font-bold text-sm">{phq9PercentChange}%</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-1.5 mb-3">
                <span className="text-5xl font-bold text-orange-600 mono">{phq9Current}</span>
                <span className="text-gray-400 text-sm mb-2">/ 27</span>
              </div>
              <div className="flex items-end gap-0.5 h-16">
                {phq9Data.map((point, idx) => {
                  const height = (point.score / 27) * 100;
                  return (
                    <div
                      key={idx}
                      className="flex-1 bg-orange-400 rounded-t hover:bg-orange-500 transition-colors"
                      style={{ height: `${height}%` }}
                      title={`S${point.session}: ${point.score}`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>Session 1</span>
                <span>Session 10</span>
              </div>
            </CardContent>
          </Card>

          {/* GAD-7 Score - Spans 2 columns */}
          <Card className="lg:col-span-2 bg-gradient-to-br from-green-100 to-green-50 border-0 shadow-md card-warm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold text-gray-700">
                    Anxiety (GAD-7)
                  </CardTitle>
                  <p className="text-xs text-gray-500 mt-1">0-21 scale</p>
                </div>
                <div className="flex items-center gap-1 text-green-600">
                  <TrendingDown className="w-4 h-4" />
                  <span className="font-bold text-sm">{gad7PercentChange}%</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-1.5 mb-3">
                <span className="text-5xl font-bold text-green-600 mono">{gad7Current}</span>
                <span className="text-gray-400 text-sm mb-2">/ 21</span>
              </div>
              <div className="flex items-end gap-0.5 h-16">
                {gad7Data.map((point, idx) => {
                  const height = (point.score / 21) * 100;
                  return (
                    <div
                      key={idx}
                      className="flex-1 bg-green-400 rounded-t hover:bg-green-500 transition-colors"
                      style={{ height: `${height}%` }}
                      title={`S${point.session}: ${point.score}`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>Session 1</span>
                <span>Session 10</span>
              </div>
            </CardContent>
          </Card>

          {/* Homework Completion - Spans 2 columns */}
          <Card className="lg:col-span-2 bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-md card-warm">
            <CardHeader>
              <CardTitle className="text-white/90 text-sm uppercase tracking-wide">
                Homework Completion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold mb-3 mono">{completionRate}%</div>
              <div className="w-full bg-white/20 rounded-full h-2.5 mb-3 overflow-hidden">
                <div
                  className="bg-white h-full rounded-full transition-all duration-500"
                  style={{ width: `${completionRate}%` }}
                />
              </div>
              <p className="text-sm text-white/80">
                {activeHomework.filter((h) => h.completed).length} of {activeHomework.length}{' '}
                completed
              </p>
            </CardContent>
          </Card>

          {/* Active Homework List - Spans 2 columns */}
          <Card className="lg:col-span-2 bg-white border-0 shadow-md card-warm">
            <CardHeader>
              <CardTitle className="text-lg">Active Homework</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {activeHomework.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    {item.completed ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                    ) : (
                      <Circle className="w-4 h-4 text-gray-300 flex-shrink-0" />
                    )}
                    <span className={item.completed ? 'text-gray-400 line-through' : 'text-gray-700'}>
                      {item.text}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Session Cards - Each takes 1 column, wraps naturally */}
          {sessions.map((session) => {
            const moodColors = {
              positive: 'bg-green-100 border-green-200',
              neutral: 'bg-blue-100 border-blue-200',
              low: 'bg-rose-100 border-rose-200',
            };

            const moodEmoji = {
              positive: '😊',
              neutral: '😐',
              low: '😔',
            };

            return (
              <Card
                key={session.id}
                className={`border shadow-sm session-card-warm card-warm ${
                  moodColors[session.mood as keyof typeof moodColors]
                }`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-lg font-bold text-gray-900">{session.date}</div>
                      <div className="text-xs text-gray-500">{session.duration}</div>
                    </div>
                    <span className="text-2xl">{moodEmoji[session.mood as keyof typeof moodEmoji]}</span>
                  </div>
                  {session.milestone && (
                    <Badge className="bg-amber-200 text-amber-900 border-0 mt-2 text-xs">
                      <Sparkles className="w-3 h-3 mr-1" />
                      {session.milestone}
                    </Badge>
                  )}
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm text-gray-700 leading-relaxed">{session.topics}</div>
                  <div className="text-sm font-medium text-blue-600">{session.strategy}</div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {session.actions.slice(0, 2).map((action, i) => (
                      <span
                        key={i}
                        className="text-xs bg-gray-700 text-white px-2 py-0.5 rounded-full"
                      >
                        {action}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Timeline at Bottom */}
        <Card className="mt-6 bg-white border-0 shadow-md">
          <CardHeader>
            <CardTitle className="text-lg">Session Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-gradient-to-b from-orange-300 via-green-300 to-blue-300" />
              <div className="space-y-4">
                {sessions.slice(0, 6).map((session) => (
                  <div key={session.id} className="relative pl-10 flex items-center gap-3">
                    <div
                      className={`absolute left-1.5 w-4 h-4 rounded-full ${
                        session.milestone
                          ? 'bg-amber-400 shimmer ring-4 ring-amber-200'
                          : session.mood === 'positive'
                          ? 'bg-green-400'
                          : session.mood === 'neutral'
                          ? 'bg-blue-400'
                          : 'bg-rose-400'
                      }`}
                    />
                    <div className="flex-1 flex items-baseline gap-3">
                      <span className="font-semibold text-sm text-gray-900">{session.date}</span>
                      <span className="text-xs text-gray-500">{session.topics}</span>
                      {session.milestone && (
                        <Badge className="bg-amber-100 text-amber-800 text-xs border-0">
                          {session.milestone}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
