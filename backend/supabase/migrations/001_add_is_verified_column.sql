-- ============================================================================
-- Migration: Add is_verified column to users table
-- ============================================================================
-- Purpose: Add email verification support to users table
--          Required by seed_demo_v4 function
--
-- Date: 2025-12-28
-- ============================================================================

-- Add is_verified column if it doesn't exist
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- Update existing users to be verified (backwards compatibility)
UPDATE users
SET is_verified = TRUE
WHERE is_verified IS NULL;

-- ============================================================================
-- Verification query (run after migration):
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'users' AND column_name = 'is_verified';
-- ============================================================================
