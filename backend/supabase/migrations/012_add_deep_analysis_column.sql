-- Migration: Add deep_analysis JSONB column for Wave 2 structured data
-- Date: 2026-01-01
-- Description: Stores structured therapeutic analysis for cumulative context

ALTER TABLE therapy_sessions
ADD COLUMN deep_analysis JSONB NULL,
ADD COLUMN deep_analyzed_at TIMESTAMP NULL;

-- Add comments for clarity
COMMENT ON COLUMN therapy_sessions.deep_analysis IS 'Structured therapeutic analysis (progress, insights, skills, relationship, recommendations)';
COMMENT ON COLUMN therapy_sessions.deep_analyzed_at IS 'Timestamp when deep analysis was completed';

-- Index for querying sessions with deep analysis
CREATE INDEX idx_therapy_sessions_deep_analyzed
ON therapy_sessions(deep_analyzed_at)
WHERE deep_analysis IS NOT NULL;
