# Day 3: AI Note Extraction Implementation Plan

## Overview

This plan implements AI-powered extraction of structured clinical notes from therapy session transcripts. We'll build a complete backend system with FastAPI, Neon PostgreSQL database, and OpenAI-based extraction that transforms raw transcripts into actionable insights for therapists and patients.

## Current State Analysis

### What Exists (Day 1-2 Complete)
- Working audio transcription pipeline in `audio-transcription-pipeline/`
- `src/pipeline.py` - CPU/API version using OpenAI Whisper
- Output: JSON with segments, timestamps, and full transcript text
- Python 3.14 environment with pydub, OpenAI client, python-dotenv
- `.env` file with `OPENAI_API_KEY` configured

### What's Missing
- No database (need to create Neon PostgreSQL)
- No backend API (need FastAPI application)
- No data models or schemas
- No AI extraction logic
- No persistence layer for transcripts or extracted notes
- No test data for realistic testing

### Key Constraints
- Must integrate with existing transcription pipeline
- Using OpenAI API (already configured) for extraction
- Cloud-first: Neon PostgreSQL for database
- Python 3.14 compatibility required

## Desired End State

After completing this plan, you will have:

1. **Database**: Neon PostgreSQL with complete schema for sessions, notes, strategies, triggers, and action items
2. **Backend API**: FastAPI application with endpoints for:
   - Uploading audio and creating sessions
   - Triggering transcription
   - Extracting notes from transcripts
   - Retrieving session data and notes
3. **AI Extraction**: OpenAI-powered extraction service that generates:
   - Structured clinical notes (topics, strategies, triggers, etc.)
   - Therapist-facing clinical summaries
   - Patient-facing friendly summaries
4. **Test Suite**: Realistic test transcripts and automated tests
5. **Integration**: Seamless connection between transcription pipeline and note extraction

### Success Verification
```bash
# Upload audio → Get back session with extracted notes
curl -X POST http://localhost:8000/api/sessions/upload -F "file=@test.mp3"
# Returns: session_id

# Check session status (should show "processed" when complete)
curl http://localhost:8000/api/sessions/{session_id}
# Returns: full session data with extracted_notes

# Get just the notes
curl http://localhost:8000/api/sessions/{session_id}/notes
# Returns: structured ExtractedNotes with all fields populated
```

## What We're NOT Doing

- Frontend UI (that's Day 4)
- Real-time streaming transcription
- Multi-user authentication (single-user MVP for now)
- Advanced pattern detection across sessions
- Crisis detection/alerting system
- Background job queues (processing will be synchronous)
- Docker containerization (local dev setup)
- Production deployment configuration

## Implementation Approach

We'll build in phases, testing each layer before moving to the next:

1. **Foundation**: Database schema + Neon setup
2. **Data Models**: Pydantic schemas for all entities
3. **AI Extraction**: OpenAI-based note extraction service
4. **FastAPI Backend**: API layer with all endpoints
5. **Integration**: Connect pipeline → API → extraction → storage
6. **Testing**: End-to-end tests with realistic data

Each phase builds on the previous one and can be verified independently.

---

## Phase 1: Database Foundation

### Overview
Set up Neon PostgreSQL and create complete database schema for sessions, extracted notes, and longitudinal tracking.

### Changes Required

#### 1.1 Neon PostgreSQL Setup

**Task**: Create Neon project and get connection string

**Steps**:
1. Go to https://neon.tech and sign up (free tier)
2. Create new project: "therapybridge-dev"
3. Copy connection string from dashboard
4. Add to `.env` file

**File**: `audio-transcription-pipeline/.env`
**Changes**: Add database connection

```bash
# Existing
OPENAI_API_KEY=sk-xxx

# Add these
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/therapybridge?sslmode=require
NEON_PROJECT_ID=xxx
```

#### 1.2 Database Schema Migration

**File**: `backend/migrations/001_initial_schema.sql`
**Changes**: Create complete schema

```sql
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
    ('therapist@therapybridge.com', 'Dr. Sarah Johnson', 'therapist')
RETURNING id;  -- Save this ID for patient creation

-- Seed test patient (update therapist_id with the ID from above)
INSERT INTO patients (name, email, therapist_id) VALUES
    ('Test Patient', 'patient@example.com', 'THERAPIST_UUID_HERE');
```

#### 1.3 Database Connection Helper

**File**: `backend/app/database.py`
**Changes**: Create database connection pool and session management

```python
"""
Database connection and session management
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

# Convert postgres:// to postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL queries (disable in production)
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (for testing)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection pool"""
    await engine.dispose()
```

### Success Criteria

#### Automated Verification:
- [ ] Neon project created and accessible
- [ ] Connection string works: `psql $DATABASE_URL -c "SELECT version();"`
- [ ] Migration applies cleanly: `psql $DATABASE_URL -f backend/migrations/001_initial_schema.sql`
- [ ] All tables created: `psql $DATABASE_URL -c "\dt"`
- [ ] Seed data inserted: `psql $DATABASE_URL -c "SELECT * FROM users;"`

#### Manual Verification:
- [ ] Can connect to Neon dashboard and see tables
- [ ] Test user and patient records visible in database
- [ ] All indexes created properly

**Implementation Note**: After completing automated verification and confirming all checks pass, pause for manual verification before proceeding to Phase 2.

---

## Phase 2: Data Models & Schemas

### Overview
Create Pydantic models for all data structures used in the API and AI extraction.

### Changes Required

#### 2.1 Core Pydantic Schemas

**File**: `backend/app/models/schemas.py`
**Changes**: Create all data models

```python
"""
Pydantic schemas for API requests/responses and AI extraction
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class UserRole(str, Enum):
    therapist = "therapist"
    patient = "patient"


class SessionStatus(str, Enum):
    pending = "pending"
    uploading = "uploading"
    transcribing = "transcribing"
    transcribed = "transcribed"
    extracting_notes = "extracting_notes"
    processed = "processed"
    failed = "failed"


class MoodLevel(str, Enum):
    very_low = "very_low"
    low = "low"
    neutral = "neutral"
    positive = "positive"
    very_positive = "very_positive"


class StrategyStatus(str, Enum):
    introduced = "introduced"  # First time mentioned
    practiced = "practiced"    # Actively used in session
    assigned = "assigned"      # Given as homework
    reviewed = "reviewed"      # Discussed effectiveness


class ActionItemStatus(str, Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


# ============================================================================
# AI Extraction Schemas
# ============================================================================

class Strategy(BaseModel):
    """A coping strategy or therapeutic technique"""
    name: str = Field(..., description="Name of strategy (e.g., 'Box breathing')")
    category: str = Field(..., description="Category (e.g., 'Breathing technique')")
    status: StrategyStatus
    context: str = Field(..., description="Brief description of how it came up")


class Trigger(BaseModel):
    """A situation or event that causes distress"""
    trigger: str = Field(..., description="The trigger (e.g., 'Team meetings')")
    context: str = Field(..., description="How it was discussed")
    severity: Optional[str] = Field(None, description="mild, moderate, or severe")


class ActionItem(BaseModel):
    """Homework or task assigned to patient"""
    task: str = Field(..., description="What to do")
    category: str = Field(..., description="homework, reflection, behavioral, etc.")
    details: Optional[str] = Field(None, description="Additional context")


class SignificantQuote(BaseModel):
    """Important statement from patient"""
    quote: str = Field(..., description="The actual quote")
    context: str = Field(..., description="Why it's significant")
    timestamp_start: Optional[float] = Field(None, description="When in session (seconds)")


class RiskFlag(BaseModel):
    """Safety concern that needs attention"""
    type: str = Field(..., description="self_harm, suicidal_ideation, crisis, etc.")
    evidence: str = Field(..., description="What triggered this flag")
    severity: str = Field(..., description="low, medium, or high")


class ExtractedNotes(BaseModel):
    """Complete set of AI-extracted notes from a session"""

    # Core content
    key_topics: List[str] = Field(..., description="Main subjects discussed (3-7 items)")
    topic_summary: str = Field(..., description="2-3 sentence overview")

    # Clinical data
    strategies: List[Strategy] = Field(default_factory=list)
    emotional_themes: List[str] = Field(default_factory=list)
    triggers: List[Trigger] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)

    # Insights
    significant_quotes: List[SignificantQuote] = Field(default_factory=list)
    session_mood: MoodLevel
    mood_trajectory: str = Field(..., description="improving, declining, stable, or fluctuating")

    # Continuity
    follow_up_topics: List[str] = Field(default_factory=list)
    unresolved_concerns: List[str] = Field(default_factory=list)

    # Safety
    risk_flags: List[RiskFlag] = Field(default_factory=list)

    # Summaries
    therapist_notes: str = Field(..., description="Clinical summary for therapist (150-200 words)")
    patient_summary: str = Field(..., description="Friendly summary for patient (100-150 words)")


# ============================================================================
# Database Models (API representations)
# ============================================================================

class TranscriptSegment(BaseModel):
    """A single segment of transcribed speech"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # "Therapist" or "Client"


class SessionBase(BaseModel):
    """Base session data"""
    patient_id: UUID
    session_date: datetime


class SessionCreate(SessionBase):
    """Request to create a new session"""
    pass


class SessionResponse(SessionBase):
    """Complete session data returned by API"""
    id: UUID
    therapist_id: UUID
    duration_seconds: Optional[int] = None

    audio_filename: Optional[str] = None
    audio_url: Optional[str] = None

    transcript_text: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None

    extracted_notes: Optional[ExtractedNotes] = None
    therapist_summary: Optional[str] = None
    patient_summary: Optional[str] = None
    risk_flags: Optional[List[RiskFlag]] = None

    status: SessionStatus
    error_message: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PatientBase(BaseModel):
    """Base patient data"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PatientCreate(PatientBase):
    """Request to create a new patient"""
    therapist_id: UUID


class PatientResponse(PatientBase):
    """Patient data returned by API"""
    id: UUID
    therapist_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# API Request/Response Models
# ============================================================================

class ExtractNotesRequest(BaseModel):
    """Request to extract notes from a transcript"""
    transcript: str
    segments: Optional[List[TranscriptSegment]] = None


class ExtractNotesResponse(BaseModel):
    """Response from note extraction"""
    extracted_notes: ExtractedNotes
    processing_time: float


class SessionStatusUpdate(BaseModel):
    """Update session status"""
    status: SessionStatus
    error_message: Optional[str] = None
```

### Success Criteria

#### Automated Verification:
- [ ] All models importable: `python -c "from backend.app.models.schemas import *"`
- [ ] Pydantic validation works: `python -m pytest backend/tests/test_schemas.py`
- [ ] JSON serialization/deserialization works correctly
- [ ] Enum values validate properly

#### Manual Verification:
- [ ] All required fields defined correctly
- [ ] Optional fields have sensible defaults
- [ ] Descriptions are clear and helpful

**Implementation Note**: After automated tests pass, manually review the schema definitions before proceeding to Phase 3.

---

## Phase 3: AI Extraction Service

### Overview
Implement the core AI extraction logic using OpenAI's GPT-4 to analyze transcripts and generate structured notes.

### Changes Required

#### 3.1 OpenAI Extraction Service

**File**: `backend/app/services/note_extraction.py`
**Changes**: Create AI extraction service

```python
"""
AI-powered note extraction from therapy session transcripts
"""
import json
import time
from typing import Dict, Optional
from openai import OpenAI
from app.models.schemas import ExtractedNotes, TranscriptSegment
import os
from dotenv import load_dotenv

load_dotenv()


EXTRACTION_PROMPT = """You are an AI assistant helping extract structured clinical information from therapy session transcripts. Your role is to identify key therapeutic content while being accurate and not hallucinating information that isn't present.

Analyze the following therapy session transcript and extract:

1. **Key Topics** - Main subjects discussed (list of 3-7 items)
2. **Topic Summary** - 2-3 sentence overview of what the session covered
3. **Strategies/Techniques** - Any coping strategies, therapeutic techniques, or tools mentioned. For each, note:
   - Name of strategy
   - Category (breathing, cognitive, behavioral, mindfulness, interpersonal, etc.)
   - Status (introduced, practiced, assigned, or reviewed)
   - Brief context
4. **Emotional Themes** - Dominant emotions expressed (anxiety, sadness, anger, hope, frustration, etc.)
5. **Triggers Identified** - Situations, people, or events that cause distress. Include:
   - The trigger
   - Context of how it was discussed
   - Severity if discernible (mild, moderate, severe)
6. **Action Items** - Homework or tasks assigned, things to try before next session
7. **Significant Quotes** - 2-3 direct quotes from the patient that capture important insights or breakthroughs
8. **Session Mood** - Overall emotional tone (very_low, low, neutral, positive, very_positive)
9. **Mood Trajectory** - Did mood improve, decline, stay stable, or fluctuate during session?
10. **Follow-up Topics** - Issues that should be revisited in future sessions
11. **Unresolved Concerns** - Topics brought up but not fully addressed
12. **Risk Flags** - ANY mentions of self-harm, suicidal thoughts, harm to others, or crisis situations. Be vigilant but don't over-flag.

Also generate:
- **Therapist Summary** - A clinical summary (150-200 words) written for the therapist's records
- **Patient Summary** - A warm, supportive summary (100-150 words) written directly to the patient in second person ("You discussed...")

IMPORTANT:
- Only extract information that is actually present in the transcript
- Do not infer or assume information not explicitly stated
- If something is unclear, note the uncertainty
- Be especially careful with risk flags - only flag clear concerns
- Use exact quotes when possible for significant statements

Return your response as valid JSON matching this structure:
{
  "key_topics": ["topic1", "topic2", ...],
  "topic_summary": "string",
  "strategies": [
    {"name": "string", "category": "string", "status": "string", "context": "string"}
  ],
  "emotional_themes": ["emotion1", "emotion2", ...],
  "triggers": [
    {"trigger": "string", "context": "string", "severity": "string"}
  ],
  "action_items": [
    {"task": "string", "category": "string", "details": "string"}
  ],
  "significant_quotes": [
    {"quote": "string", "context": "string"}
  ],
  "session_mood": "string",
  "mood_trajectory": "string",
  "follow_up_topics": ["topic1", ...],
  "unresolved_concerns": ["concern1", ...],
  "risk_flags": [
    {"type": "string", "evidence": "string", "severity": "string"}
  ],
  "therapist_notes": "string",
  "patient_summary": "string"
}

TRANSCRIPT:
{transcript}
"""


class NoteExtractionService:
    """Service for extracting structured notes from transcripts using OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Using GPT-4 for better reasoning

    async def extract_notes_from_transcript(
        self,
        transcript: str,
        segments: Optional[list[TranscriptSegment]] = None
    ) -> ExtractedNotes:
        """
        Extract structured clinical notes from a therapy session transcript.

        Args:
            transcript: Full text of the session
            segments: Optional list of timestamped segments

        Returns:
            ExtractedNotes object with all structured data
        """
        print(f"[NoteExtraction] Starting extraction for {len(transcript)} character transcript")
        start_time = time.time()

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a clinical psychology expert who extracts structured data from therapy transcripts. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(transcript=transcript)
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent extraction
            response_format={"type": "json_object"}  # Force JSON output
        )

        # Parse response
        response_text = response.choices[0].message.content

        # Handle potential markdown code blocks (shouldn't happen with json_object mode)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON
        extracted_data = json.loads(response_text)

        # Create Pydantic model (this validates the structure)
        notes = ExtractedNotes(**extracted_data)

        elapsed = time.time() - start_time
        print(f"[NoteExtraction] Completed in {elapsed:.2f}s")
        print(f"  - Topics: {len(notes.key_topics)}")
        print(f"  - Strategies: {len(notes.strategies)}")
        print(f"  - Action items: {len(notes.action_items)}")
        print(f"  - Risk flags: {len(notes.risk_flags)}")

        return notes

    def estimate_cost(self, transcript: str) -> Dict[str, float]:
        """
        Estimate the cost of extracting notes from a transcript.

        GPT-4o pricing (as of Dec 2024):
        - Input: $2.50 per 1M tokens
        - Output: $10.00 per 1M tokens

        Rough estimate: ~1 token per 4 characters
        """
        # Rough token estimation
        prompt_tokens = len(EXTRACTION_PROMPT) / 4 + len(transcript) / 4
        output_tokens = 1500  # Estimated output size

        input_cost = (prompt_tokens / 1_000_000) * 2.50
        output_cost = (output_tokens / 1_000_000) * 10.00
        total_cost = input_cost + output_cost

        return {
            "estimated_input_tokens": int(prompt_tokens),
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": round(total_cost, 4)
        }


# Singleton instance
_extraction_service: Optional[NoteExtractionService] = None


def get_extraction_service() -> NoteExtractionService:
    """Get or create the extraction service singleton"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = NoteExtractionService()
    return _extraction_service
```

#### 3.2 Test Transcript Generator

**File**: `backend/tests/fixtures/sample_transcripts.py`
**Changes**: Create realistic test data

```python
"""
Sample therapy session transcripts for testing
"""

SAMPLE_TRANSCRIPT_1 = """
Therapist: Hi Sarah, good to see you. How have you been since our last session?

Patient: It's been a rough week honestly. Work has been really stressful. My manager assigned me this huge project with an impossible deadline, and I've been staying late every night.

Therapist: That sounds exhausting. How has that been affecting you?

Patient: I haven't been sleeping well. I keep waking up at 3am thinking about everything I need to do. And then I'm exhausted during the day but can't focus.

Therapist: The sleep disruption is significant. Last time we talked about the box breathing technique. Have you had a chance to try that when you wake up at night?

Patient: I tried it a couple times. It helped a little, but then my mind just goes right back to the work stuff.

Therapist: That's actually good progress - you tried it and noticed some benefit. The racing thoughts are hard. What specifically runs through your mind?

Patient: Mostly that I'm going to fail. That everyone will see I can't handle this. My manager already seems disappointed in me.

Therapist: Those sound like some pretty harsh self-judgments. Do you have evidence that your manager is disappointed?

Patient: Not really... she hasn't said anything negative. I guess I just assume because she's been quiet.

Therapist: That's an interesting observation. We call that mind-reading in CBT - assuming we know what others think without evidence. What might be another explanation for her being quiet?

Patient: I guess she could just be busy too. Everyone's stressed about this project.

Therapist: Exactly. I'd like you to try something this week. When you notice yourself assuming the worst about what others think, pause and ask yourself - what's the evidence? And what's another possible explanation?

Patient: Okay, I can try that.

Therapist: Great. And for the sleep - let's add something. When you wake up at 3am, try the box breathing first, then if your mind is still racing, get up and write down your worries for 5 minutes. Get them out of your head and onto paper. Then go back to bed.

Patient: That's interesting. I've never tried writing them down.

Therapist: It can help externalize the worries so they're not spinning in your head. How are you feeling right now, talking about all this?

Patient: A little better actually. It helps to talk about it and have some things to try.

Therapist: I'm glad. You're dealing with a lot, and you're showing up and working on it. That takes strength. Same time next week?

Patient: Yes, that works. Thank you.
"""

EXPECTED_EXTRACTION_1 = {
    "key_topics": [
        "Work stress and deadline pressure",
        "Sleep disruption and insomnia",
        "Self-critical thoughts and catastrophizing",
        "Cognitive distortions (mind-reading)"
    ],
    "strategies": [
        {
            "name": "Box breathing",
            "category": "Breathing technique",
            "status": "reviewed",
            "context": "Patient tried it for nighttime waking, found it somewhat helpful"
        },
        {
            "name": "Cognitive restructuring - evidence checking",
            "category": "Cognitive",
            "status": "introduced",
            "context": "Identifying mind-reading and checking evidence for assumptions"
        },
        {
            "name": "Worry journaling",
            "category": "Behavioral",
            "status": "assigned",
            "context": "Write down worries when waking at 3am to externalize thoughts"
        }
    ],
    "triggers": [
        {
            "trigger": "Work deadlines and high-pressure projects",
            "context": "Large project with tight deadline causing stress and sleep issues",
            "severity": "moderate"
        },
        {
            "trigger": "Perceived manager disappointment",
            "context": "Manager's quietness interpreted as negative feedback",
            "severity": "mild"
        }
    ],
    "action_items": [
        {
            "task": "Practice evidence-checking when assuming others' thoughts",
            "category": "cognitive",
            "details": "When mind-reading: ask 'what's the evidence?' and 'what's another explanation?'"
        },
        {
            "task": "Try worry journaling at 3am wakings",
            "category": "behavioral",
            "details": "Box breathing first, then 5 min writing if mind still racing, then back to bed"
        }
    ],
    "session_mood": "low",
    "mood_trajectory": "improving"
}
```

### Success Criteria

#### Automated Verification:
- [ ] Service imports successfully: `python -c "from backend.app.services.note_extraction import get_extraction_service"`
- [ ] Can extract notes from sample: `python backend/tests/test_extraction_service.py`
- [ ] JSON output validates against ExtractedNotes schema
- [ ] All expected fields are populated
- [ ] Cost estimation function returns reasonable values

#### Manual Verification:
- [ ] Extracted topics match transcript content
- [ ] Strategies are correctly categorized
- [ ] Action items are actionable and specific
- [ ] Therapist summary is clinical and concise
- [ ] Patient summary is warm and encouraging
- [ ] No hallucinated information

**Implementation Note**: After automated tests pass, manually review several extraction outputs for quality before proceeding to Phase 4.

---

## Phase 4: FastAPI Backend

### Overview
Build the complete FastAPI application with all endpoints for session management, transcription, and note extraction.

### Changes Required

#### 4.1 Main FastAPI Application

**File**: `backend/app/main.py`
**Changes**: Create FastAPI app with all configuration

```python
"""
TherapyBridge Backend API
FastAPI application for therapy session management and AI note extraction
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db, close_db
from app.routers import sessions, patients
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting TherapyBridge API...")
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down TherapyBridge API...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="TherapyBridge API",
    description="AI-powered therapy session management and note extraction",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TherapyBridge API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "transcription": "available",
            "extraction": "available"
        }
    }
```

#### 4.2 Sessions Router

**File**: `backend/app/routers/sessions.py`
**Changes**: Create session management endpoints

```python
"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
import os
import shutil
from pathlib import Path
import asyncio

from app.database import get_db
from app.models.schemas import (
    SessionCreate, SessionResponse, SessionStatus,
    ExtractedNotes, ExtractNotesResponse
)
from app.services.note_extraction import get_extraction_service
from app.models import db_models

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """
    Background task to process audio: transcribe → extract notes

    This runs asynchronously after audio upload.
    """
    from app.services.transcription import transcribe_audio_file

    try:
        # Update status: transcribing
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()

        # Step 1: Transcribe audio
        print(f"[Pipeline] Transcribing session {session_id}...")
        transcript_result = await transcribe_audio_file(audio_path)

        # Save transcript to database
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                transcript_text=transcript_result["full_text"],
                transcript_segments=transcript_result["segments"],
                duration_seconds=int(transcript_result.get("duration", 0)),
                status=SessionStatus.transcribed.value
            )
        )
        await db.commit()

        # Step 2: Extract notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.extracting_notes.value)
        )
        await db.commit()

        print(f"[Pipeline] Extracting notes for session {session_id}...")
        extraction_service = get_extraction_service()
        notes = await extraction_service.extract_notes_from_transcript(
            transcript=transcript_result["full_text"],
            segments=transcript_result.get("segments")
        )

        # Save extracted notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                extracted_notes=notes.model_dump(),
                therapist_summary=notes.therapist_notes,
                patient_summary=notes.patient_summary,
                risk_flags=[flag.model_dump() for flag in notes.risk_flags],
                status=SessionStatus.processed.value
            )
        )
        await db.commit()

        print(f"[Pipeline] Session {session_id} processed successfully!")

        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"[Pipeline] Cleaned up audio file: {audio_path}")

    except Exception as e:
        print(f"[Pipeline] Error processing session {session_id}: {str(e)}")

        # Update status to failed
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()


@router.post("/upload", response_model=SessionResponse)
async def upload_audio_session(
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file to create a new session

    This will:
    1. Create session record in database
    2. Save audio file
    3. Start background processing (transcription + extraction)

    Returns immediately with session_id and status="uploading"
    """
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    # Check file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"File type {file_ext} not supported. Allowed: {allowed_extensions}")

    # Create session in database
    from app.models.db_models import Session
    from datetime import datetime

    # Get therapist (for MVP, use the seeded therapist)
    therapist_result = await db.execute(
        select(db_models.User).where(db_models.User.role == "therapist").limit(1)
    )
    therapist = therapist_result.scalar_one_or_none()
    if not therapist:
        raise HTTPException(500, "No therapist found in database")

    new_session = db_models.Session(
        patient_id=patient_id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename=file.filename,
        status=SessionStatus.uploading.value
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Save audio file
    file_path = UPLOAD_DIR / f"{new_session.id}{file_ext}"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"[Upload] Saved audio file: {file_path}")

        # Update session with file path
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(audio_url=str(file_path))
        )
        await db.commit()

        # Start background processing
        background_tasks.add_task(
            process_audio_pipeline,
            session_id=new_session.id,
            audio_path=str(file_path),
            db=db
        )

        return SessionResponse.model_validate(new_session)

    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()

        raise HTTPException(500, f"Failed to save audio file: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get complete session data including extracted notes"""
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    return SessionResponse.model_validate(session)


@router.get("/{session_id}/notes", response_model=ExtractedNotes)
async def get_session_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get just the extracted notes for a session"""
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.extracted_notes:
        raise HTTPException(404, "Notes not yet extracted for this session")

    return ExtractedNotes(**session.extracted_notes)


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    patient_id: Optional[UUID] = None,
    status: Optional[SessionStatus] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List sessions with optional filters"""
    query = select(db_models.Session).order_by(db_models.Session.session_date.desc())

    if patient_id:
        query = query.where(db_models.Session.patient_id == patient_id)

    if status:
        query = query.where(db_models.Session.status == status.value)

    query = query.limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("/{session_id}/extract-notes", response_model=ExtractNotesResponse)
async def manually_extract_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger note extraction for a transcribed session

    Useful for re-processing or if automatic extraction failed
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.transcript_text:
        raise HTTPException(400, "Session must be transcribed before extracting notes")

    # Extract notes
    import time
    start_time = time.time()

    extraction_service = get_extraction_service()
    notes = await extraction_service.extract_notes_from_transcript(
        transcript=session.transcript_text,
        segments=session.transcript_segments
    )

    processing_time = time.time() - start_time

    # Save to database
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(
            extracted_notes=notes.model_dump(),
            therapist_summary=notes.therapist_notes,
            patient_summary=notes.patient_summary,
            risk_flags=[flag.model_dump() for flag in notes.risk_flags],
            status=SessionStatus.processed.value
        )
    )
    await db.commit()

    return ExtractNotesResponse(
        extracted_notes=notes,
        processing_time=processing_time
    )
```

#### 4.3 Database Models (SQLAlchemy)

**File**: `backend/app/models/db_models.py`
**Changes**: Create ORM models

```python
"""
SQLAlchemy ORM models for database tables
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, UUID as SQLUUID, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("patients.id"))
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
    session_date = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)

    audio_filename = Column(String(255))
    audio_url = Column(Text)

    transcript_text = Column(Text)
    transcript_segments = Column(JSONB)

    extracted_notes = Column(JSONB)
    therapist_summary = Column(Text)
    patient_summary = Column(Text)
    risk_flags = Column(JSONB)

    status = Column(String(50), default="pending")
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
```

#### 4.4 Transcription Service Integration

**File**: `backend/app/services/transcription.py`
**Changes**: Wrapper for existing pipeline

```python
"""
Audio transcription service - wrapper for existing pipeline
"""
import sys
from pathlib import Path
from typing import Dict

# Add audio-transcription-pipeline to path
PIPELINE_DIR = Path(__file__).parent.parent.parent.parent / "audio-transcription-pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from src.pipeline import AudioTranscriptionPipeline


async def transcribe_audio_file(audio_path: str) -> Dict:
    """
    Transcribe audio file using the existing pipeline

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with segments, full_text, language, duration
    """
    pipeline = AudioTranscriptionPipeline()
    result = pipeline.process(audio_path)
    return result
```

### Success Criteria

#### Automated Verification:
- [ ] FastAPI app starts: `uvicorn backend.app.main:app --reload`
- [ ] Health check returns 200: `curl http://localhost:8000/health`
- [ ] OpenAPI docs accessible: `curl http://localhost:8000/docs`
- [ ] All endpoints registered correctly
- [ ] Database connection works on startup

#### Manual Verification:
- [ ] Can access interactive API docs at http://localhost:8000/docs
- [ ] All endpoints are documented
- [ ] Request/response schemas are correct
- [ ] Background tasks are registered properly

**Implementation Note**: After the server starts successfully and all automated checks pass, test the endpoints manually using the Swagger UI before proceeding to Phase 5.

---

## Phase 5: End-to-End Integration & Testing

### Overview
Connect all components and create comprehensive tests with realistic data.

### Changes Required

#### 5.1 Dependencies File

**File**: `backend/requirements.txt`
**Changes**: Add all backend dependencies

```txt
# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6  # For file uploads

# Database
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0  # PostgreSQL async driver
alembic==1.13.1  # Migrations (future use)

# OpenAI
openai>=1.59.5

# Environment
python-dotenv>=1.0.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0  # For testing async FastAPI

# Audio pipeline dependencies (reuse from transcription pipeline)
pydub==0.25.1
audioop-lts>=0.2.1
```

#### 5.2 Backend Project Structure

**File**: `backend/README.md`
**Changes**: Setup instructions

```markdown
# TherapyBridge Backend

FastAPI backend for therapy session management and AI note extraction.

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# OpenAI
OPENAI_API_KEY=sk-xxx
```

### 3. Initialize Database

```bash
# Connect to Neon and run migration
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

### 4. Run Server

```bash
uvicorn app.main:app --reload
```

API will be available at http://localhost:8000

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── database.py          # DB connection
│   ├── models/
│   │   ├── schemas.py       # Pydantic models
│   │   └── db_models.py     # SQLAlchemy models
│   ├── routers/
│   │   ├── sessions.py      # Session endpoints
│   │   └── patients.py      # Patient endpoints
│   └── services/
│       ├── transcription.py # Audio transcription
│       └── note_extraction.py # AI extraction
├── tests/
│   ├── test_extraction.py
│   └── fixtures/
│       └── sample_transcripts.py
├── migrations/
│   └── 001_initial_schema.sql
└── requirements.txt
```

## API Endpoints

### Sessions
- `POST /api/sessions/upload` - Upload audio file
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/notes` - Get extracted notes
- `GET /api/sessions` - List all sessions
- `POST /api/sessions/{id}/extract-notes` - Manually trigger extraction

### Health
- `GET /` - Simple health check
- `GET /health` - Detailed health status
```

#### 5.3 Integration Test

**File**: `backend/tests/test_integration.py`
**Changes**: End-to-end test

```python
"""
Integration tests for complete audio → notes pipeline
"""
import pytest
from httpx import AsyncClient
from pathlib import Path
import asyncio
from app.main import app
from app.database import init_db, close_db


@pytest.fixture
async def client():
    """Test client for FastAPI"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await init_db()
        yield client
        await close_db()


@pytest.mark.asyncio
async def test_complete_pipeline(client):
    """
    Test complete pipeline: upload → transcribe → extract → retrieve
    """
    # 1. Check health
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # 2. Upload audio (using sample file)
    sample_audio = Path("../audio-transcription-pipeline/tests/samples/onemintestvid.mp3")
    if not sample_audio.exists():
        pytest.skip("Sample audio file not found")

    with open(sample_audio, "rb") as f:
        response = await client.post(
            "/api/sessions/upload",
            files={"file": ("test.mp3", f, "audio/mpeg")},
            params={"patient_id": "test-patient-id"}  # Use seeded patient
        )

    assert response.status_code == 200
    session = response.json()
    session_id = session["id"]
    assert session["status"] == "uploading"

    # 3. Wait for processing to complete (poll status)
    max_wait = 300  # 5 minutes max
    wait_interval = 5  # Check every 5 seconds

    for _ in range(max_wait // wait_interval):
        response = await client.get(f"/api/sessions/{session_id}")
        session = response.json()

        if session["status"] == "processed":
            break
        elif session["status"] == "failed":
            pytest.fail(f"Processing failed: {session.get('error_message')}")

        await asyncio.sleep(wait_interval)

    assert session["status"] == "processed", "Session did not complete processing"

    # 4. Verify transcript exists
    assert session["transcript_text"] is not None
    assert len(session["transcript_text"]) > 0

    # 5. Verify extracted notes exist
    assert session["extracted_notes"] is not None
    notes = session["extracted_notes"]

    assert len(notes["key_topics"]) > 0
    assert notes["topic_summary"]
    assert notes["therapist_notes"]
    assert notes["patient_summary"]
    assert notes["session_mood"] in ["very_low", "low", "neutral", "positive", "very_positive"]

    # 6. Get notes separately
    response = await client.get(f"/api/sessions/{session_id}/notes")
    assert response.status_code == 200
    notes_only = response.json()

    assert notes_only == notes

    print("\n✅ Integration test passed!")
    print(f"  Session ID: {session_id}")
    print(f"  Topics: {notes['key_topics']}")
    print(f"  Mood: {notes['session_mood']}")
    print(f"  Strategies: {len(notes['strategies'])}")
```

#### 5.4 Unit Test for Extraction

**File**: `backend/tests/test_extraction_service.py`
**Changes**: Test AI extraction in isolation

```python
"""
Unit tests for note extraction service
"""
import pytest
from app.services.note_extraction import NoteExtractionService
from app.models.schemas import ExtractedNotes
from tests.fixtures.sample_transcripts import SAMPLE_TRANSCRIPT_1


@pytest.mark.asyncio
async def test_extract_notes_basic():
    """Test basic note extraction from sample transcript"""
    service = NoteExtractionService()

    notes = await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)

    # Verify it returns correct type
    assert isinstance(notes, ExtractedNotes)

    # Verify required fields are populated
    assert len(notes.key_topics) >= 3
    assert len(notes.topic_summary) > 50
    assert notes.therapist_notes
    assert notes.patient_summary
    assert notes.session_mood

    # Verify strategies were extracted
    assert len(notes.strategies) > 0
    assert notes.strategies[0].name
    assert notes.strategies[0].category

    # Verify action items
    assert len(notes.action_items) > 0

    # Print for manual review
    print("\n" + "="*60)
    print("EXTRACTED NOTES")
    print("="*60)
    print(f"\nTopics: {', '.join(notes.key_topics)}")
    print(f"\nSummary: {notes.topic_summary}")
    print(f"\nStrategies:")
    for s in notes.strategies:
        print(f"  - {s.name} ({s.category}) - {s.status}")
    print(f"\nAction Items:")
    for a in notes.action_items:
        print(f"  - {a.task}")
    print(f"\nMood: {notes.session_mood} ({notes.mood_trajectory})")
    print("\n" + "="*60)


@pytest.mark.asyncio
async def test_cost_estimation():
    """Test cost estimation for extraction"""
    service = NoteExtractionService()

    cost = service.estimate_cost(SAMPLE_TRANSCRIPT_1)

    assert cost["estimated_input_tokens"] > 0
    assert cost["estimated_output_tokens"] > 0
    assert cost["estimated_cost_usd"] > 0
    assert cost["estimated_cost_usd"] < 0.50  # Should be pennies

    print(f"\nEstimated cost: ${cost['estimated_cost_usd']:.4f}")
```

### Success Criteria

#### Automated Verification:
- [ ] Backend dependencies install: `pip install -r backend/requirements.txt`
- [ ] Server starts without errors: `uvicorn backend.app.main:app --reload`
- [ ] Unit tests pass: `pytest backend/tests/test_extraction_service.py -v`
- [ ] Integration test passes: `pytest backend/tests/test_integration.py -v`
- [ ] All API endpoints return correct status codes

#### Manual Verification:
- [ ] Upload a real audio file via Swagger UI
- [ ] Session progresses through all statuses (uploading → transcribing → extracting_notes → processed)
- [ ] Extracted notes are high quality and accurate
- [ ] Therapist summary is clinical and professional
- [ ] Patient summary is warm and encouraging
- [ ] No sensitive data leakage in logs
- [ ] Cost per session is reasonable (<$0.05)

**Implementation Note**: After all automated tests pass, manually test the complete pipeline with a real therapy session audio file before considering this phase complete.

---

## Testing Strategy

### Unit Tests
- Pydantic schema validation (`test_schemas.py`)
- AI extraction service (`test_extraction_service.py`)
- Database models and queries (`test_database.py`)

### Integration Tests
- Full pipeline: upload → transcribe → extract (`test_integration.py`)
- API endpoint behavior (`test_api.py`)

### Manual Testing Steps

1. **Upload Test Audio**
   ```bash
   # Using curl
   curl -X POST http://localhost:8000/api/sessions/upload \
     -F "file=@test-session.mp3" \
     -F "patient_id=PATIENT_UUID"
   ```

2. **Monitor Processing**
   ```bash
   # Check status
   curl http://localhost:8000/api/sessions/SESSION_ID
   ```

3. **Verify Output Quality**
   - Read therapist summary - should be clinical and actionable
   - Read patient summary - should be encouraging and clear
   - Check strategies - correctly categorized?
   - Check action items - specific and achievable?
   - Check risk flags - any false positives?

4. **Test Edge Cases**
   - Very short session (<2 min)
   - Very long session (>60 min)
   - Poor audio quality
   - Session with no clear action items
   - Session with multiple risk flags

## Performance Considerations

### Expected Processing Times
| Duration | Transcription | Extraction | Total |
|----------|--------------|------------|-------|
| 5 min    | ~30-45s      | ~15-20s    | ~1 min |
| 30 min   | ~3-4 min     | ~20-30s    | ~5 min |
| 60 min   | ~6-8 min     | ~30-40s    | ~9 min |

### Cost per Session
- Whisper API: $0.006/min → **~$0.18** for 30-min session
- GPT-4o extraction: ~$0.01-0.03 per session
- **Total: ~$0.20 per 30-minute session**

### Optimization Opportunities (Future)
- Use background job queue (Celery/Redis) instead of FastAPI BackgroundTasks
- Cache common extraction patterns
- Use GPT-4o-mini for simpler extractions (~70% cost reduction)
- Implement rate limiting to prevent API overuse

## Migration Notes

### From Development to Production
1. **Environment Variables**
   - Move `.env` to secure secret management (AWS Secrets Manager, etc.)
   - Use separate Neon projects for dev/staging/prod

2. **Database**
   - Enable connection pooling
   - Set up automated backups
   - Implement migration strategy (Alembic)

3. **API**
   - Add authentication (Auth.js/NextAuth)
   - Enable rate limiting
   - Set up monitoring (Sentry, DataDog)
   - Configure CORS for production domain

4. **Storage**
   - Move audio files to S3 instead of local filesystem
   - Implement file cleanup policy

## References

- Original requirements: `Project MDs/Day3-AI-Note-Extraction-Plan.md`
- Dashboard plan: `Project MDs/Dashboard-Plan.md`
- Main project docs: `Project MDs/TherapyBridge.md`
- Transcription pipeline: `audio-transcription-pipeline/README.md`

---

**Created**: 2025-12-10
**Status**: Ready for implementation
**Estimated Time**: 6-8 hours for full implementation
