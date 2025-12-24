-- Migration: Add prose_analysis field for patient-facing narrative summaries
-- Date: 2025-12-23
-- Description: Stores 500-750 word prose generated from structured deep_analysis

ALTER TABLE therapy_sessions
ADD COLUMN prose_analysis TEXT NULL,
ADD COLUMN prose_generated_at TIMESTAMP NULL;

-- Add comment for clarity
COMMENT ON COLUMN therapy_sessions.prose_analysis IS 'Patient-facing prose narrative (500-750 words) generated from structured deep_analysis';
COMMENT ON COLUMN therapy_sessions.prose_generated_at IS 'Timestamp when prose was last generated';

-- Index for querying sessions with prose
CREATE INDEX idx_therapy_sessions_prose_generated
ON therapy_sessions(prose_generated_at)
WHERE prose_analysis IS NOT NULL;
