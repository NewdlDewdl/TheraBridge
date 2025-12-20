'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, TrendingDown, TrendingUp, Minus, CheckCircle2, Circle } from 'lucide-react';

/**
 * MOCKUP 3: "Modern Clinical"
 *
 * Design Philosophy:
 * - Data-focused interface with crisp, clean edges
 * - Cooler color palette for professional, clinical feel
 * - Geometric typography with emphasis on readability
 * - Medium spacing for efficient information density
 *
 * Color Palette (modern clinical):
 * - Primary: Deep teal (#2C7A7B) - professional, clinical trust
 * - Secondary: Muted purple (#6B46C1) - analytical, measured
 * - Accent: Slate gray (#475569) - neutral, objective
 * - Background: Cool white (#F8FAFC) - clean, clinical
 */

export default function DashboardMockupModernClinical() {
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
      date: 'Dec 17',
      duration: '50m',
      mood: 'positive',
      topics: ['Boundaries', 'Self-advocacy'],
      strategy: 'Assertiveness training',
      actions: ['Set boundary', 'Journal wins'],
    },
    {
      id: 9,
      date: 'Dec 10',
      duration: '45m',
      mood: 'positive',
      topics: ['Self-worth', 'Relationships'],
      strategy: 'Laddering technique',
      actions: ['Self-compassion', 'Behavioral exp.'],
      milestone: 'Breakthrough',
    },
    {
      id: 8,
      date: 'Dec 3',
      duration: '48m',
      mood: 'neutral',
      topics: ['Work stress', 'Anxiety'],
      strategy: '4-7-8 breathing',
      actions: ['Breathing 2x', 'Track triggers'],
    },
    {
      id: 7,
      date: 'Nov 26',
      duration: '45m',
      mood: 'neutral',
      topics: ['Family', 'Holiday stress'],
      strategy: 'Grounding',
      actions: ['5-4-3-2-1', 'Boundaries'],
      milestone: 'New strategy',
    },
    {
      id: 6,
      date: 'Nov 19',
      duration: '50m',
      mood: 'low',
      topics: ['Loneliness', 'Isolation'],
      strategy: 'Behavioral activation',
      actions: ['Social event', 'Call friend'],
    },
    {
      id: 5,
      date: 'Nov 12',
      duration: '45m',
      mood: 'neutral',
      topics: ['Sleep', 'Rumination'],
      strategy: 'Sleep hygiene',
      actions: ['No screens', 'Journaling'],
      milestone: 'PHQ-9 -30%',
    },
    {
      id: 4,
      date: 'Nov 5',
      duration: '50m',
      mood: 'low',
      topics: ['Breakup', 'Grief'],
      strategy: 'Emotional validation',
      actions: ['Allow feelings', 'Support group'],
    },
    {
      id: 3,
      date: 'Oct 29',
      duration: '45m',
      mood: 'low',
      topics: ['Core beliefs'],
      strategy: 'CBT thought records',
      actions: ['Track thoughts', 'Challenge beliefs'],
    },
    {
      id: 2,
      date: 'Oct 22',
      duration: '50m',
      mood: 'neutral',
      topics: ['Goals', 'Treatment plan'],
      strategy: 'Goal setting',
      actions: ['Define 3 goals', 'Track progress'],
      milestone: 'Treatment plan',
    },
    {
      id: 1,
      date: 'Oct 15',
      duration: '60m',
      mood: 'neutral',
      topics: ['Intake', 'History'],
      strategy: 'Assessment',
      actions: ['Forms', 'Baseline'],
      milestone: 'First session',
    },
  ];

  const homeworkTasks = [
    { id: 1, text: 'Set boundary with friend about time commitments', completed: false },
    { id: 2, text: 'Journal daily wins and moments of self-advocacy', completed: false },
    { id: 3, text: 'Practice self-compassion when negative thoughts arise', completed: true },
    { id: 4, text: 'Conduct behavioral experiment with trusted friend', completed: false },
    { id: 5, text: 'Use 4-7-8 breathing when feeling anxious 2x daily', completed: true },
    { id: 6, text: 'Track anxiety triggers in journal', completed: true },
  ];

  const completionRate = (homeworkTasks.filter((t) => t.completed).length / homeworkTasks.length) * 100;

  const getMoodColor = (mood: string) => {
    switch (mood) {
      case 'positive':
        return 'border-l-emerald-500 bg-emerald-50/50';
      case 'neutral':
        return 'border-l-slate-400 bg-slate-50/50';
      case 'low':
        return 'border-l-rose-400 bg-rose-50/50';
      default:
        return 'border-l-slate-300';
    }
  };

  const getMoodEmoji = (mood: string) => {
    switch (mood) {
      case 'positive':
        return '😊';
      case 'neutral':
        return '😐';
      case 'low':
        return '😔';
      default:
        return '😐';
    }
  };

  const getTrendIcon = (data: Array<{ score: number }>) => {
    const firstScore = data[0].score;
    const lastScore = data[data.length - 1].score;
    const improvement = ((firstScore - lastScore) / firstScore) * 100;

    if (improvement > 0) return <TrendingDown className="w-5 h-5 text-emerald-600" />;
    if (improvement < 0) return <TrendingUp className="w-5 h-5 text-rose-600" />;
    return <Minus className="w-5 h-5 text-slate-400" />;
  };

  const getImprovementPercent = (data: Array<{ score: number }>) => {
    const firstScore = data[0].score;
    const lastScore = data[data.length - 1].score;
    return Math.round(((firstScore - lastScore) / firstScore) * 100);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Main Container - Modern Clinical */}
      <div className="max-w-[1400px] mx-auto px-10 py-10">
        {/* Header - Clean and data-focused */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 tracking-tight">Clinical Progress</h1>
          <p className="text-slate-600 text-base">10-session treatment outcome data</p>
        </header>

        {/* Layout: 75% Main Content | 25% Sidebar */}
        <div className="flex gap-6">
          {/* MAIN CONTENT AREA (75%) */}
          <div className="flex-1">
            {/* Clinical Progress Cards - Side by side */}
            <div className="grid grid-cols-2 gap-5 mb-8">
              {/* PHQ-9 Depression Card */}
              <Card className="border-slate-200 shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold text-slate-700">PHQ-9 Depression</CardTitle>
                    {getTrendIcon(phq9Data)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-5xl font-bold text-slate-900">{phq9Data[phq9Data.length - 1].score}</span>
                    <span className="text-sm text-slate-500">/ 27</span>
                    <Badge variant="outline" className="ml-auto bg-emerald-50 text-emerald-700 border-emerald-200">
                      {getImprovementPercent(phq9Data)}% improvement
                    </Badge>
                  </div>

                  {/* Mini chart - Data visualization */}
                  <div className="flex items-end gap-1 h-16 mt-4">
                    {phq9Data.map((point, idx) => {
                      const maxScore = Math.max(...phq9Data.map((d) => d.score));
                      const height = (point.score / maxScore) * 100;
                      return (
                        <div key={idx} className="flex-1 flex flex-col justify-end">
                          <div
                            className="w-full bg-gradient-to-t from-teal-700 to-teal-500 rounded-t transition-all hover:opacity-80"
                            style={{ height: `${height}%` }}
                            title={`Session ${point.session}: ${point.score}`}
                          />
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 mt-2">
                    <span>Session 1</span>
                    <span>Session 10</span>
                  </div>
                </CardContent>
              </Card>

              {/* GAD-7 Anxiety Card */}
              <Card className="border-slate-200 shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold text-slate-700">GAD-7 Anxiety</CardTitle>
                    {getTrendIcon(gad7Data)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-2 mb-4">
                    <span className="text-5xl font-bold text-slate-900">{gad7Data[gad7Data.length - 1].score}</span>
                    <span className="text-sm text-slate-500">/ 21</span>
                    <Badge variant="outline" className="ml-auto bg-emerald-50 text-emerald-700 border-emerald-200">
                      {getImprovementPercent(gad7Data)}% improvement
                    </Badge>
                  </div>

                  {/* Mini chart */}
                  <div className="flex items-end gap-1 h-16 mt-4">
                    {gad7Data.map((point, idx) => {
                      const maxScore = Math.max(...gad7Data.map((d) => d.score));
                      const height = (point.score / maxScore) * 100;
                      return (
                        <div key={idx} className="flex-1 flex flex-col justify-end">
                          <div
                            className="w-full bg-gradient-to-t from-purple-700 to-purple-500 rounded-t transition-all hover:opacity-80"
                            style={{ height: `${height}%` }}
                            title={`Session ${point.session}: ${point.score}`}
                          />
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 mt-2">
                    <span>Session 1</span>
                    <span>Session 10</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* To-Do Card - Merged homework completion */}
            <Card className="mb-8 border-slate-200 shadow-md">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold text-slate-900">Homework Tasks</CardTitle>
                  <span className="text-2xl font-bold text-slate-700">{Math.round(completionRate)}%</span>
                </div>
              </CardHeader>
              <CardContent>
                {/* Progress bar */}
                <div className="mb-5">
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-teal-600 to-purple-600 transition-all"
                      style={{ width: `${completionRate}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {homeworkTasks.filter((t) => t.completed).length} of {homeworkTasks.length} completed
                  </p>
                </div>

                {/* Task list - Compact clinical style */}
                <div className="space-y-2.5">
                  {homeworkTasks.map((task) => (
                    <div key={task.id} className="flex items-start gap-3">
                      {task.completed ? (
                        <CheckCircle2 className="w-4 h-4 text-teal-600 mt-0.5 flex-shrink-0" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-300 mt-0.5 flex-shrink-0" />
                      )}
                      <span
                        className={`text-sm ${
                          task.completed ? 'text-slate-400 line-through' : 'text-slate-700'
                        }`}
                      >
                        {task.text}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Session Cards Grid - 2-column masonry */}
            <div>
              <h2 className="text-xl font-semibold text-slate-900 mb-4 tracking-tight">Session History</h2>
              <div className="grid grid-cols-2 gap-4">
                {sessions.map((session) => (
                  <Card
                    key={session.id}
                    className={`border-l-4 ${getMoodColor(
                      session.mood
                    )} border-t-0 border-r-0 border-b-0 shadow-sm hover:shadow-md transition-all cursor-pointer relative overflow-visible`}
                  >
                    {/* Milestone badge on top border */}
                    {session.milestone && (
                      <div className="absolute -top-3 left-4">
                        <Badge className="bg-amber-100 text-amber-900 border border-amber-200 shadow-sm px-3 py-0.5 text-xs font-medium">
                          ⭐ {session.milestone}
                        </Badge>
                      </div>
                    )}

                    <CardContent className="p-4">
                      {/* Metadata row */}
                      <div className="flex items-center gap-2 text-xs text-slate-500 mb-3 pt-1">
                        <span className="font-medium text-slate-700">{session.date}</span>
                        <span>•</span>
                        <span>{session.duration}</span>
                        <span>•</span>
                        <span>{getMoodEmoji(session.mood)}</span>
                      </div>

                      {/* Two-column split */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Left: Topics */}
                        <div>
                          <div className="space-y-1">
                            {session.topics.map((topic, idx) => (
                              <p key={idx} className="text-xs text-slate-600 leading-relaxed">
                                {topic}
                              </p>
                            ))}
                          </div>
                        </div>

                        {/* Right: Strategy & Actions */}
                        <div>
                          <p className="text-xs font-semibold text-teal-700 mb-2">{session.strategy}</p>
                          <div className="space-y-1">
                            {session.actions.map((action, idx) => (
                              <p key={idx} className="text-xs text-slate-500">
                                • {action}
                              </p>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* SIDEBAR (25%) - Vertical Timeline */}
          <aside className="w-80 flex-shrink-0">
            <Card className="sticky top-6 border-slate-200 shadow-md">
              <CardHeader>
                <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4">
                <div className="space-y-4">
                  {sessions.map((session, idx) => (
                    <div key={session.id} className="relative flex gap-3">
                      {/* Connector line */}
                      {idx < sessions.length - 1 && (
                        <div className="absolute left-2 top-6 w-0.5 h-full bg-gradient-to-b from-teal-300 via-purple-300 to-slate-200" />
                      )}

                      {/* Timeline dot */}
                      <div className="relative z-10">
                        {session.milestone ? (
                          <div className="w-5 h-5 rounded-full bg-amber-400 flex items-center justify-center shadow-sm">
                            <span className="text-xs">⭐</span>
                          </div>
                        ) : (
                          <div
                            className={`w-4 h-4 rounded-full ${
                              session.mood === 'positive'
                                ? 'bg-emerald-400'
                                : session.mood === 'neutral'
                                ? 'bg-slate-400'
                                : 'bg-rose-400'
                            }`}
                          />
                        )}
                      </div>

                      {/* Timeline content */}
                      <div className="flex-1 pb-2">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-medium text-slate-700">{session.date}</span>
                          <span className="text-xs text-slate-400">{getMoodEmoji(session.mood)}</span>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed">
                          {session.topics[0]}
                        </p>
                        {session.milestone && (
                          <p className="text-xs text-amber-700 italic mt-1">✨ {session.milestone}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
}
