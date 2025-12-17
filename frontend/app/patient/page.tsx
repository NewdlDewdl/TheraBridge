'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/EmptyState';
import { MoodIndicator } from '@/components/MoodIndicator';
import { PatientDashboardSkeleton } from '@/components/skeletons';
import { Calendar, Target, CheckCircle, MessageCircle } from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';
import { useState, useEffect } from 'react';

// This is a simplified example - in production, you'd:
// 1. Add authentication to identify the patient
// 2. Fetch their specific sessions
// 3. Display patient_summary instead of therapist_notes

export default function PatientPortal() {
  const [isLoading, setIsLoading] = useState(true);

  // Simulate loading time
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return <PatientDashboardSkeleton />;
  }

  // Mock data for demonstration - replace with real API calls
  const mockSessions = [
    {
      id: '1',
      date: '2025-12-10',
      duration: 1380,
      summary: 'You discussed feeling unlovable after your recent breakup. We explored how past experiences might be influencing these feelings and started working on recognizing your inherent worth.',
      mood: 'low' as const,
      actionItems: ['Practice self-compassion when negative thoughts arise', 'Conduct behavioral experiment with a friend'],
    },
    {
      id: '2',
      date: '2025-12-03',
      duration: 1500,
      summary: 'We focused on managing anxiety around social situations. You practiced breathing techniques and started identifying triggers that make you feel most anxious.',
      mood: 'neutral' as const,
      actionItems: ['Use 4-7-8 breathing when feeling anxious', 'Keep a journal of anxiety triggers'],
    },
  ];

  const activeStrategies = [
    { name: 'Laddering', category: 'cognitive' },
    { name: '4-7-8 Breathing', category: 'breathing' },
    { name: 'Behavioral Experiments', category: 'behavioral' },
  ];

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Welcome back</h2>
        <p className="text-muted-foreground">Track your therapy progress and action items</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{mockSessions.length}</p>
                <p className="text-sm text-muted-foreground">Total Sessions</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <Target className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeStrategies.length}</p>
                <p className="text-sm text-muted-foreground">Active Strategies</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Strategies */}
      {activeStrategies.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Your Active Strategies</CardTitle>
            <CardDescription>Techniques you&apos;re currently working with</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {activeStrategies.map((strategy, index) => (
                <li key={index} className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium">{strategy.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {strategy.category}
                  </Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : (
        <EmptyState
          icon={Target}
          heading="No active strategies yet"
          description="Work with your therapist to identify strategies for your treatment plan"
          iconSize="md"
          showCard
        />
      )}

      {/* Action Items */}
      {mockSessions.length > 0 && mockSessions.some(s => s.actionItems.length > 0) ? (
        <Card>
          <CardHeader>
            <CardTitle>Your Action Items</CardTitle>
            <CardDescription>Things to practice between sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockSessions.flatMap((session) =>
                session.actionItems.map((item, index) => (
                  <div key={`${session.id}-${index}`} className="flex items-start gap-3">
                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-gray-300" />
                    <span className="text-sm">{item}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <EmptyState
          icon={CheckCircle}
          heading="No action items yet"
          description="Your therapist will share action items after your sessions"
          iconSize="md"
          showCard
        />
      )}

      {/* Recent Sessions */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Recent Sessions</h3>
        {mockSessions.length > 0 ? (
          <div className="space-y-4">
            {mockSessions.map((session) => (
              <Card key={session.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{formatDate(session.date)}</CardTitle>
                      <CardDescription className="flex items-center gap-1 mt-1">
                        <Calendar className="w-3 h-3" />
                        {formatDuration(session.duration)}
                      </CardDescription>
                    </div>
                    <MoodIndicator mood={session.mood} showLabel={false} size="sm" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">{session.summary}</p>
                  <div className="space-y-2">
                    <p className="text-xs font-medium">Action Items:</p>
                    <ul className="space-y-1">
                      {session.actionItems.map((item, index) => (
                        <li key={index} className="text-sm flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={MessageCircle}
            heading="No sessions yet"
            description="Schedule your first session with your therapist to get started"
            iconSize="md"
            showCard
          />
        )}
      </div>
    </div>
  );
}
