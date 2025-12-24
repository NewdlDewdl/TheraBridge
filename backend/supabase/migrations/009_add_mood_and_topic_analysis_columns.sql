-- Migration: Add Mood Analysis and Topic Extraction Columns
-- Description: Adds columns for Wave 1 AI analysis (mood + topics)

-- Add mood analysis columns
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS mood_score DECIMAL(3,1) CHECK (mood_score >= 0 AND mood_score <= 10),
ADD COLUMN IF NOT EXISTS mood_confidence DECIMAL(3,2) CHECK (mood_confidence >= 0 AND mood_confidence <= 1),
ADD COLUMN IF NOT EXISTS mood_rationale TEXT,
ADD COLUMN IF NOT EXISTS mood_indicators JSONB,
ADD COLUMN IF NOT EXISTS emotional_tone TEXT,
ADD COLUMN IF NOT EXISTS mood_analyzed_at TIMESTAMP;

-- Add topic extraction columns (already exist in some deployments, so using IF NOT EXISTS)
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS topics JSONB,
ADD COLUMN IF NOT EXISTS action_items JSONB,
ADD COLUMN IF NOT EXISTS technique TEXT,
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS extraction_confidence DECIMAL(3,2) CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
ADD COLUMN IF NOT EXISTS topics_extracted_at TIMESTAMP;

-- Add breakthrough detection columns (may already exist)
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS has_breakthrough BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS breakthrough_label TEXT,
ADD COLUMN IF NOT EXISTS breakthrough_data JSONB,
ADD COLUMN IF NOT EXISTS breakthrough_analyzed_at TIMESTAMP;

-- Add comments for documentation
COMMENT ON COLUMN therapy_sessions.mood_score IS 'AI-analyzed mood score (0.0-10.0): 0=severe distress, 10=excellent';
COMMENT ON COLUMN therapy_sessions.mood_confidence IS 'Confidence level of mood analysis (0.0-1.0)';
COMMENT ON COLUMN therapy_sessions.mood_rationale IS 'Clinical reasoning for mood score';
COMMENT ON COLUMN therapy_sessions.mood_indicators IS 'Key emotional/clinical indicators from session';
COMMENT ON COLUMN therapy_sessions.emotional_tone IS 'Overall emotional tone description';

COMMENT ON COLUMN therapy_sessions.topics IS 'Main discussion topics (1-2 items)';
COMMENT ON COLUMN therapy_sessions.action_items IS 'Homework/action items from session';
COMMENT ON COLUMN therapy_sessions.technique IS 'Primary therapeutic technique used';
COMMENT ON COLUMN therapy_sessions.summary IS 'Brief session summary (2 sentences)';
COMMENT ON COLUMN therapy_sessions.extraction_confidence IS 'Confidence level of topic extraction (0.0-1.0)';

COMMENT ON COLUMN therapy_sessions.has_breakthrough IS 'Whether session contains a transformative moment';
COMMENT ON COLUMN therapy_sessions.breakthrough_label IS 'Type of breakthrough (e.g., "First Insight", "Emotional Release")';
COMMENT ON COLUMN therapy_sessions.breakthrough_data IS 'Structured breakthrough details';
