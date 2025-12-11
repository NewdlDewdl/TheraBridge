-- TherapyBridge Initial Database Schema
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (simplified for MVP - single therapist for now)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('therapist', 'patient')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    therapist_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id),
    therapist_id UUID REFERENCES users(id),
    session_date TIMESTAMP NOT NULL,
    duration_seconds INTEGER,

    -- Audio file storage
    audio_filename VARCHAR(255),
    audio_url TEXT,

    -- Transcription data
    transcript_text TEXT,
    transcript_segments JSONB,  -- Array of {start, end, text, speaker}

    -- Extracted notes
    extracted_notes JSONB,  -- Full ExtractedNotes object
    therapist_summary TEXT,
    patient_summary TEXT,
    risk_flags JSONB,  -- Array of risk flag objects

    -- Processing status
    status VARCHAR(50) DEFAULT 'pending',
    -- Status values: pending, uploading, transcribing, transcribed, extracting_notes, processed, failed
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- Index for common queries
CREATE INDEX idx_sessions_patient_date ON sessions(patient_id, session_date DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_therapist_date ON sessions(therapist_id, session_date DESC);

-- Patient strategies tracking (longitudinal data)
CREATE TABLE patient_strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    session_id UUID REFERENCES sessions(id),  -- Where first introduced

    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- breathing, cognitive, behavioral, mindfulness, etc.
    status VARCHAR(50),  -- introduced, practiced, assigned, reviewed

    -- Effectiveness tracking
    effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
    times_mentioned INTEGER DEFAULT 1,

    -- Timestamps
    first_introduced TIMESTAMP DEFAULT NOW(),
    last_mentioned TIMESTAMP DEFAULT NOW(),

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_patient_strategies ON patient_strategies(patient_id, last_mentioned DESC);

-- Patient triggers tracking
CREATE TABLE patient_triggers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    session_id UUID REFERENCES sessions(id),  -- Where first identified

    trigger VARCHAR(255) NOT NULL,
    severity VARCHAR(50),  -- mild, moderate, severe

    times_mentioned INTEGER DEFAULT 1,
    last_mentioned TIMESTAMP DEFAULT NOW(),

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_patient_triggers ON patient_triggers(patient_id, last_mentioned DESC);

-- Action items / homework
CREATE TABLE action_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    session_id UUID REFERENCES sessions(id) NOT NULL,

    task TEXT NOT NULL,
    category VARCHAR(100),  -- homework, reflection, behavioral, etc.
    status VARCHAR(50) DEFAULT 'assigned',  -- assigned, in_progress, completed, abandoned

    assigned_date TIMESTAMP DEFAULT NOW(),
    due_date TIMESTAMP,
    completed_date TIMESTAMP,

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_action_items_patient ON action_items(patient_id, status, assigned_date DESC);

-- Seed data for testing (single therapist)
INSERT INTO users (email, name, role) VALUES
    ('therapist@therapybridge.com', 'Dr. Sarah Johnson', 'therapist');

-- Seed test patient (get therapist_id from above insert)
INSERT INTO patients (name, email, therapist_id)
SELECT 'Test Patient', 'patient@example.com', id
FROM users
WHERE email = 'therapist@therapybridge.com';
