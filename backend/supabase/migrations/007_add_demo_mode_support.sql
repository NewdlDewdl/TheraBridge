-- Migration: Add demo mode support
-- Date: 2025-12-23
-- Purpose: Enable temporary demo users with token-based access

-- Add demo fields to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS demo_token UUID UNIQUE,
ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS demo_created_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS demo_expires_at TIMESTAMP;

-- Index for fast demo token lookups
CREATE INDEX IF NOT EXISTS idx_users_demo_token
ON users(demo_token)
WHERE demo_token IS NOT NULL;

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_users_demo_expiry
ON users(demo_expires_at)
WHERE is_demo = TRUE;

-- Comments for documentation
COMMENT ON COLUMN users.demo_token IS 'Unique UUID for demo user authentication (stored in localStorage)';
COMMENT ON COLUMN users.is_demo IS 'Flag indicating temporary demo user (auto-deleted after 24h)';
COMMENT ON COLUMN users.demo_created_at IS 'Timestamp when demo user was created';
COMMENT ON COLUMN users.demo_expires_at IS 'Timestamp when demo user should be deleted (24h after creation)';
