/**
 * Type definitions for TherapyBridge Dashboard
 * - Session data structures
 * - Task and milestone types
 * - Timeline and mood tracking types
 */

export type MoodType = 'positive' | 'neutral' | 'low';

export interface Session {
  id: string;
  date: string;
  duration: string;
  therapist: string;
  mood: MoodType;
  topics: string[];
  strategy: string;
  actions: string[];
  milestone?: Milestone;
  transcript?: TranscriptEntry[];
  patientSummary?: string;
}

export interface Milestone {
  title: string;
  description: string;
}

export interface TranscriptEntry {
  speaker: 'Therapist' | 'Patient';
  text: string;
}

export interface Task {
  id: string;
  text: string;
  completed: boolean;
  sessionId: string;
  sessionDate: string;
}

/**
 * Chart data point types for different progress metrics.
 * Each metric type has a specific data structure for Recharts.
 */
export interface MoodTrendDataPoint {
  session: string;
  mood: number;
}

export interface HomeworkImpactDataPoint {
  week: string;
  completion: number;
  mood: number;
}

export interface SessionConsistencyDataPoint {
  week: string;
  attended: number;
}

export interface StrategyEffectivenessDataPoint {
  strategy: string;
  effectiveness: number;
}

// Union type for all chart data point types
export type ChartDataPoint =
  | MoodTrendDataPoint
  | HomeworkImpactDataPoint
  | SessionConsistencyDataPoint
  | StrategyEffectivenessDataPoint;

export interface ProgressMetric {
  title: string;
  description: string;
  chartData: ChartDataPoint[];
  insight: string;
  emoji: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface TimelineEntry {
  sessionId: string;
  date: string;
  duration: string;  // e.g., "45 min"
  topic: string;
  strategy: string;  // Therapeutic technique used
  mood: MoodType;
  milestone?: Milestone;
}
