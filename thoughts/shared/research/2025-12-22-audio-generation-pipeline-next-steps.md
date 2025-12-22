---
date: 2025-12-22T09:49:16Z
researcher: NewdlDewdl
git_commit: c3730fe11392c9bd93c9e2198ac49491458df063
branch: main
repository: peerbridge proj
topic: "Audio Generation Pipeline and Frontend Integration Next Steps"
tags: [research, codebase, audio-generation, hume-ai, frontend-integration, pipeline]
status: complete
last_updated: 2025-12-22
last_updated_by: NewdlDewdl
---

# Research: Audio Generation Pipeline and Frontend Integration Next Steps

**Date**: 2025-12-22T09:49:16Z
**Researcher**: NewdlDewdl
**Git Commit**: c3730fe11392c9bd93c9e2198ac49491458df063
**Branch**: main
**Repository**: peerbridge proj

## Research Question

Figure out the next steps and various pipelines that need to be created to work with the frontend. Firstly need to generate the audio files from the existing session transcripts.

## Executive Summary

**Current State:**
- ✅ All 12 therapy session transcripts generated (11 validated, 1 needs timestamp fix)
- ✅ Supporting data files created (major_events.json, chat_messages.json)
- ✅ Frontend dashboard-v3 has mock data system with 10 sample sessions
- ⚠️ **NO audio generation implementation exists** - Hume AI TTS integration is 0% complete
- ⚠️ Session 12 has critical timestamp mismatch (ends at 5300s instead of 3000s)

**Implementation Gap:**
The codebase has comprehensive documentation and data preparation for Hume AI Octave TTS integration, but zero actual implementation code. Audio generation is the **critical missing piece** before frontend integration can proceed.

**Next Steps Priority:**
1. **IMMEDIATE**: Fix session_12_thriving.json timestamp issue
2. **HIGH PRIORITY**: Implement Hume AI TTS audio generation script
3. **MEDIUM PRIORITY**: Upload generated audio to Supabase Storage
4. **LOW PRIORITY**: Integrate mock sessions into frontend dashboard-v3

---

## Detailed Findings

### 1. Session Transcript Status

**Location:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/mock-therapy-data/sessions/`

**Completion Status:**
- 12/12 session JSON files exist
- 11/12 sessions validated and ready for audio generation
- 1/12 sessions require regeneration

**Validation Results** (`validation_results.json:4-11`):
```json
{
  "overall_status": "FAIL",
  "summary": {
    "total_files": 12,
    "passing_files": 11,
    "failing_files": 1,
    "pass_rate": "91.7%"
  }
}
```

**Critical Issue** (`validation_results.json:34-40`):
- **Session 12** (`session_12_thriving.json`) - Timestamp integrity failure
- Last segment ends at 5300.0s (88.3 minutes)
- Metadata declares duration as 3000.0s (50 minutes)
- Discrepancy: 2300 seconds (38.33 minutes)
- **Impact**: Will cause audio generation to fail
- **Action Required**: Regenerate session_12_thriving.json with corrected timestamps OR update metadata duration to 5300.0s

**Ready Sessions** (`validation_results.json:217-229`):
1. session_01_crisis_intake (60 min)
2. session_02_emotional_regulation (45 min)
3. session_03_adhd_discovery (50 min)
4. session_04_medication_start (45 min)
5. session_05_family_conflict (55 min)
6. session_06_spring_break_hope (50 min)
7. session_07_dating_anxiety (50 min)
8. session_08_relationship_boundaries (45 min)
9. session_09_coming_out_preparation (60 min)
10. session_10_coming_out_aftermath (55 min)
11. session_11_rebuilding (50 min)

**Total Ready:** 10.25 hours of validated dialogue ready for audio generation

---

### 2. Hume AI Integration Status

**Current Implementation:** 0% - Documentation only, no code exists

**What EXISTS:**
- Comprehensive documentation in `INTEGRATION_GUIDE.md:421-452`
- Voice configuration specifications:
  - SPEAKER_00 (Dr. Sarah Mitchell): Male therapist voice
  - SPEAKER_01 (Alex Chen): Non-binary/androgynous patient voice
- Pseudocode generation workflow in implementation plan
- Audio compatibility validation scripts (`validate_sessions.py:239-273`)
- External documentation reference: https://hume.ai/octave

**What DOES NOT EXIST:**
- No `.env` variables for Hume AI API keys
- No Python/JavaScript code calling Hume AI TTS API
- No HTTP client setup for Hume AI endpoints
- No audio file generation scripts
- No API credentials configuration
- No integration testing

**Data Format Ready for Hume AI:**

Each session JSON contains:
- `aligned_segments` array: Granular utterances for TTS (150-220 segments/session)
- Each segment structure:
  ```json
  {
    "start": 0.0,
    "end": 18.3,
    "text": "Hey Alex, good to see you again...",
    "speaker": "SPEAKER_00",
    "speaker_id": "SPEAKER_00"
  }
  ```

**Audio Compatibility Validated** (`validation_results.json:178-184`):
- 537 segments analyzed across 11 passing sessions
- 0 segments over 300 seconds
- 0 empty text fields
- 0 encoding issues (UTF-8 verified)
- 0 invalid speaker labels
- All segments < 500 characters (Hume AI limit)

**Planned Output Location:**
- `backend/uploads/audio/alex_chen/session_NN_YYYY-MM-DD.mp3`

---

### 3. Frontend Dashboard Integration

**Location:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/frontend/app/patient/dashboard-v3/`

**Current Mock Data System:**

**Mock Data File:** `lib/mockData.ts`
- Contains 10 therapy sessions with simplified structure
- Includes topics, strategies, actions, transcripts
- Major events integrated (4 events)
- Timeline merges sessions + events

**Mock Toggle:** `lib/usePatientSessions.ts:27`
```typescript
const USE_MOCK_DATA = true; // Toggle between mock and real API
```

**Data Structure Mismatch:**

**Dashboard Session Type** (`dashboard-v3/lib/types.ts:10-22`):
```typescript
interface Session {
  id: string;              // "s10"
  date: string;            // "Dec 17" (display format)
  duration: string;        // "50m" (human-readable)
  therapist: string;       // "Dr. Sarah Chen"
  mood: MoodType;          // 'positive' | 'neutral' | 'low'
  topics: string[];
  strategy: string;
  actions: string[];
  transcript?: TranscriptEntry[];  // Simplified format
}
```

**Pipeline Output Format** (`mock-therapy-data/sessions/session_02_emotional_regulation.json`):
```json
{
  "id": "session_02_alex_chen",
  "metadata": {
    "duration": 2700.0,
    "language": "english"
  },
  "speakers": [...],
  "segments": [...],
  "aligned_segments": [...]
}
```

**Transformation Required:**
1. Speaker role detection: `SPEAKER_00`/`SPEAKER_01` → `Therapist`/`Client`
   - Already implemented: `frontend/lib/speaker-role-detection.ts`
   - Applied in: `frontend/app/api/process/route.ts:147-166`

2. Date formatting: ISO timestamp → Display format ("Jan 17")
3. Duration conversion: Seconds (2700.0) → Human-readable ("45m")
4. Extract topics/strategies (requires GPT-4 extraction or manual mapping)
5. Simplify transcript: Keep speaker + text, optionally timestamps

**Upload Flow (Existing):**

`frontend/app/patient/dashboard-v3/upload/page.tsx` → Full upload UI exists
- File upload via `components/FileUploader.tsx`
- Processing status tracking via `contexts/ProcessingContext.tsx`
- Progress display via `components/UploadProgress.tsx`
- Results view via `components/ResultsView.tsx`

**Backend Processing Pipeline** (`frontend/app/api/process/route.ts:24`):
1. Upload audio → Supabase Storage (`api/upload/route.ts:61`)
2. Trigger async processing (`api/trigger-processing/route.ts:22`)
3. Call transcription service → `http://localhost:8000/api/transcribe`
4. Poll for completion (2-second intervals)
5. Speaker role detection (frontend fallback)
6. GPT-4 analysis for topics/mood/insights
7. Save to database with all results

**Frontend Display Components:**
- `components/SessionCard.tsx` - Grid view compact card
- `components/SessionDetail.tsx` - Fullscreen modal with transcript + analysis
- `frontend/components/TranscriptViewer.tsx` - Collapsible transcript with timestamps

---

### 4. Supporting Data Files

**Major Events** (`mock-therapy-data/major_events.json`):
- ✅ 10 events documented (7 external + 3 in-session breakthroughs)
- Structure includes: id, date, title, category, severity, summary, related_sessions
- **Frontend Integration Status**: Already integrated in dashboard-v3
  - Mixed timeline: `components/TimelineSidebar.tsx` (purple diamond icons)
  - AI chat context: `lib/chat-context.ts`
  - Event modal: `components/MajorEventModal.tsx`

**Chat Messages** (`mock-therapy-data/chat_messages.json`):
- ✅ 4 chat threads with 78 messages total
- Realistic Gen-Z texting language
- **Frontend Integration Status**: NOT currently used
  - Dashboard has separate `initialChatMessages` in `mockData.ts:258`
  - Could populate chat history or AI context examples

**Integration Guide** (`mock-therapy-data/INTEGRATION_GUIDE.md`):
- ✅ Complete step-by-step instructions for frontend integration
- Covers file placement, import statements, transform functions
- Timeline merging logic documented
- Testing verification steps included

---

### 5. Audio Processing Architecture (Existing)

**Note:** This is the **reverse direction** (audio → text), not text → audio generation.

**Location:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/audio-transcription-pipeline/`

**Service Architecture:**
- FastAPI service on port 8000
- Job-based queue system for async processing
- Stages: Preprocessing → Transcription → Diarization → Alignment → Combining

**Processing Pipeline** (`ui-web/backend/app/services/pipeline_service.py:41-260`):

1. **Transcription** (10% → 40% progress)
   - OpenAI Whisper API
   - Language: "en" (ISO-639-1)
   - Duration: ~45 seconds for 23-minute audio

2. **Speaker Diarization** (40% → 80% progress)
   - Pyannote 3.1 with 2-speaker detection
   - Requires HF_TOKEN environment variable
   - Duration: ~79 seconds

3. **Speaker Alignment** (80% → 90% progress)
   - 30% overlap threshold algorithm
   - Nearest-neighbor fallback for gaps
   - Reduces "Unknown" speakers to <2%

4. **Segment Combining** (95% → 98% progress)
   - Merges consecutive same-speaker turns
   - Reduces 150 granular → ~45 speaker turns

**Output Format:**
```json
{
  "id": "job_id",
  "status": "completed",
  "segments": [...],           // Combined speaker turns
  "aligned_segments": [...],   // Granular utterances
  "speakers": [...],
  "performance": {...}
}
```

**Storage:**
- Audio files: Supabase Storage bucket `audio-sessions`
- Path: `{patient_id}/{timestamp}.{extension}`
- Transcription results: PostgreSQL `therapy_sessions.transcript` (JSONB)

---

## Next Steps: Implementation Roadmap

### Phase 1: Fix Critical Issue (IMMEDIATE)

**Task**: Repair session_12_thriving.json timestamp mismatch

**Options:**
1. **Regenerate entire session** with correct 3000s duration
2. **Update metadata only** to match actual 5300s duration
3. **Trim segments** to fit within 3000s window

**Recommended Approach**: Regenerate session with accurate 50-minute (3000s) content
- Maintains consistency with other sessions
- Ensures audio generation will succeed
- Preserves clinical arc and breakthrough content

**Implementation:**
```bash
# Re-run session generation agent for Session 12
# Follow template from: plans/2025-12-22-parallel-transcript-generation.md
# Validate: python3 validate_sessions.py
# Confirm: validation_results.json shows 12/12 passing
```

**Success Criteria:**
- `validation_results.json` shows `"overall_status": "PASS"`
- `"failing_files": 0`
- Session 12 last segment ends at ~3000s ± 30s

---

### Phase 2: Implement Hume AI Audio Generation (HIGH PRIORITY)

**Task**: Create TTS script to generate MP3 audio from session transcripts

**Prerequisites:**
1. Hume AI API account and API key
2. Voice ID configuration (male therapist, non-binary patient)
3. Python environment with requests/httpx library

**Implementation Steps:**

**Step 2.1: Environment Setup**

Create `.env` file in `mock-therapy-data/`:
```bash
HUME_API_KEY=your_api_key_here
HUME_THERAPIST_VOICE_ID=voice_id_for_male_therapist
HUME_PATIENT_VOICE_ID=voice_id_for_nonbinary_patient
OUTPUT_DIR=../backend/uploads/audio/alex_chen
```

**Step 2.2: Create Audio Generation Script**

**File**: `mock-therapy-data/scripts/generate_audio.py`

**Pseudocode Structure:**
```python
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

HUME_API_KEY = os.getenv('HUME_API_KEY')
THERAPIST_VOICE = os.getenv('HUME_THERAPIST_VOICE_ID')
PATIENT_VOICE = os.getenv('HUME_PATIENT_VOICE_ID')
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR'))

def generate_segment_audio(segment, session_id):
    """Generate audio for single segment using Hume AI TTS"""
    voice_id = THERAPIST_VOICE if segment['speaker_id'] == 'SPEAKER_00' else PATIENT_VOICE

    response = requests.post(
        'https://api.hume.ai/v1/tts/synthesize',
        headers={'Authorization': f'Bearer {HUME_API_KEY}'},
        json={
            'text': segment['text'],
            'voice_id': voice_id,
            'format': 'mp3'
        }
    )

    segment_file = OUTPUT_DIR / session_id / f"{segment['start']}-{segment['end']}.mp3"
    segment_file.parent.mkdir(parents=True, exist_ok=True)
    segment_file.write_bytes(response.content)

    return segment_file

def combine_segments(segment_files, output_file):
    """Combine audio segments using ffmpeg"""
    # Create concat file
    concat_list = OUTPUT_DIR / 'concat_list.txt'
    with concat_list.open('w') as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file}'\n")

    # Combine with ffmpeg
    os.system(f"ffmpeg -f concat -safe 0 -i {concat_list} -c copy {output_file}")

def generate_session_audio(session_file):
    """Generate complete audio for one session"""
    with open(session_file) as f:
        session = json.load(f)

    session_id = session['id']
    print(f"Generating audio for {session_id}...")

    segment_files = []
    for i, segment in enumerate(session['aligned_segments']):
        print(f"  Segment {i+1}/{len(session['aligned_segments'])}")
        seg_file = generate_segment_audio(segment, session_id)
        segment_files.append(seg_file)

    output_file = OUTPUT_DIR / session['filename']
    combine_segments(segment_files, output_file)

    print(f"✅ Generated: {output_file}")
    return output_file

def main():
    sessions_dir = Path('sessions')
    for session_file in sorted(sessions_dir.glob('session_*.json')):
        generate_session_audio(session_file)

if __name__ == '__main__':
    main()
```

**Step 2.3: Batch Generation**

**Command:**
```bash
cd mock-therapy-data
python scripts/generate_audio.py
```

**Expected Output:**
```
Generating audio for session_01_alex_chen...
  Segment 1/213
  Segment 2/213
  ...
✅ Generated: ../backend/uploads/audio/alex_chen/session_01_2025-01-10.mp3
...
✅ Generated: ../backend/uploads/audio/alex_chen/session_12_2025-05-16.mp3
```

**Success Criteria:**
- 12 MP3 files in `backend/uploads/audio/alex_chen/`
- File sizes: 15-25MB per session (45-60 minutes)
- Audio duration matches `metadata.duration` exactly (±5 seconds)
- Therapist/patient voices distinguishable
- No audio gaps >2 seconds between segments

---

### Phase 3: Upload Audio to Supabase Storage (MEDIUM PRIORITY)

**Task**: Move generated audio files to Supabase Storage for production use

**Current Storage Setup** (`supabase/schema.sql:154-167`):
- Bucket: `audio-sessions`
- Access: Private (authentication required)
- Path format: `{patient_id}/{timestamp}.{extension}`

**Implementation:**

**Script**: `mock-therapy-data/scripts/upload_to_supabase.py`

```python
from supabase import create_client
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')  # Service key for backend operations
)

PATIENT_ID = 'alex_chen'  # Or UUID from database
AUDIO_DIR = Path('../backend/uploads/audio/alex_chen')

for audio_file in sorted(AUDIO_DIR.glob('session_*.mp3')):
    file_path = f"{PATIENT_ID}/{audio_file.name}"

    with open(audio_file, 'rb') as f:
        supabase.storage.from_('audio-sessions').upload(
            file_path,
            f,
            file_options={"content-type": "audio/mpeg"}
        )

    print(f"✅ Uploaded: {file_path}")
```

**Alternative**: Use Supabase CLI
```bash
supabase storage cp backend/uploads/audio/alex_chen/*.mp3 audio-sessions/alex_chen/
```

**Success Criteria:**
- All 12 audio files visible in Supabase Storage dashboard
- Public URLs accessible (with authentication)
- File sizes match local files

---

### Phase 4: Integrate Sessions into Frontend Dashboard (LOW PRIORITY)

**Task**: Replace/augment mock data with real session data

**Current Mock Data**: `frontend/app/patient/dashboard-v3/lib/mockData.ts:19-178`

**Implementation Approach:**

**Option A: Add Real Sessions Alongside Mock Data**
- Keep existing 10 mock sessions
- Add 12 new sessions from mock-therapy-data
- Total: 22 sessions in timeline

**Option B: Replace Mock Data Entirely**
- Remove existing mock sessions
- Import all 12 real sessions
- Transform to dashboard format

**Recommended**: Option A (hybrid approach for testing)

**Step 4.1: Create Transform Utility**

**File**: `frontend/app/patient/dashboard-v3/lib/transformSession.ts`

```typescript
import type { Session as DashboardSession } from './types';

interface PipelineSession {
  id: string;
  metadata: {
    duration: number;
    language: string;
  };
  speakers: Array<{id: string; total_duration: number}>;
  segments: Array<{
    start: number;
    end: number;
    text: string;
    speaker: string;
  }>;
}

export function transformPipelineSession(
  pipelineSession: PipelineSession,
  extractedNotes: {
    topics: string[];
    strategy: string;
    action_items: string[];
    mood: string;
    patient_summary: string;
  }
): DashboardSession {
  // Parse date from session ID or metadata
  const sessionDate = parseSessionDate(pipelineSession.id);

  return {
    id: pipelineSession.id,
    date: formatDate(sessionDate), // "Jan 17"
    duration: formatDuration(pipelineSession.metadata.duration), // "45m"
    therapist: "Dr. Sarah Mitchell",
    mood: mapMood(extractedNotes.mood), // Convert to 'positive'|'neutral'|'low'
    topics: extractedNotes.topics,
    strategy: extractedNotes.strategy,
    actions: extractedNotes.action_items,
    transcript: pipelineSession.segments.map(seg => ({
      speaker: seg.speaker === 'SPEAKER_00' ? 'Therapist' : 'Patient',
      text: seg.text
    })),
    patientSummary: extractedNotes.patient_summary
  };
}

function mapMood(backendMood: string): 'positive' | 'neutral' | 'low' {
  if (backendMood === 'very_positive' || backendMood === 'positive') return 'positive';
  if (backendMood === 'very_low' || backendMood === 'low') return 'low';
  return 'neutral';
}
```

**Step 4.2: Import Session Data**

**Option 1**: Static import (development)
```typescript
// mockData.ts
import session01 from '../../../../mock-therapy-data/sessions/session_01_crisis_intake.json';
import session02 from '../../../../mock-therapy-data/sessions/session_02_emotional_regulation.json';
// ... import all 12

const realSessions = [
  session01,
  session02,
  // ...
].map(transformPipelineSession);
```

**Option 2**: API integration (production)
```typescript
// usePatientSessions.ts
const USE_MOCK_DATA = false; // Toggle to real API

// Fetches from: GET /api/v1/patients/{id}/sessions
// Backend returns sessions with audio_url, transcript, extracted_notes
```

**Step 4.3: Update Mock Data File**

Add real sessions to existing mock data:
```typescript
// mockData.ts
export const sessions: Session[] = [
  ...existingMockSessions,  // Keep for comparison
  ...realSessions           // Add from mock-therapy-data
];
```

**Step 4.4: Testing**

Verify display in dashboard:
1. Session cards render correctly
2. Mood indicators match expected values
3. Topics/strategies display properly
4. Transcript viewer shows dialogue with speaker labels
5. Timeline includes all 22 sessions chronologically
6. Major events still display correctly

**Success Criteria:**
- All 12 real sessions visible in dashboard grid
- Session detail modal opens with full transcript
- No console errors
- Mood colors match session content
- Timeline integrates sessions + major events

---

## Implementation Timeline

**Phase 1: Critical Fix** (30 minutes)
- Fix session_12_thriving.json timestamp issue
- Re-run validation
- Confirm 12/12 passing

**Phase 2: Audio Generation** (4-8 hours)
- Set up Hume AI account + API key
- Write generation script
- Test with 1 session
- Generate all 12 sessions
- Validate audio quality

**Phase 3: Supabase Upload** (30 minutes)
- Upload audio files
- Verify accessibility
- Update database records with audio URLs

**Phase 4: Frontend Integration** (2-4 hours)
- Create transform utility
- Import session data
- Test dashboard display
- Fix any styling/formatting issues

**Total Estimated Time**: 7-13 hours

---

## Code References

**Session Transcripts:**
- `mock-therapy-data/sessions/session_01_crisis_intake.json:1` - Reference format
- `mock-therapy-data/sessions/session_12_thriving.json:1` - NEEDS FIX

**Validation:**
- `mock-therapy-data/validate_sessions.py:239` - Audio compatibility checks
- `mock-therapy-data/validation_results.json:34` - Session 12 error details

**Documentation:**
- `mock-therapy-data/INTEGRATION_GUIDE.md:421` - Hume AI voice configuration
- `mock-therapy-data/plans/2025-12-22-parallel-transcript-generation.md:558` - Compatibility test script

**Frontend:**
- `frontend/app/patient/dashboard-v3/lib/types.ts:10` - Dashboard Session interface
- `frontend/app/patient/dashboard-v3/lib/mockData.ts:19` - Current mock sessions
- `frontend/lib/speaker-role-detection.ts:1` - Speaker role assignment logic
- `frontend/components/TranscriptViewer.tsx:39` - Transcript rendering

**Backend Processing:**
- `frontend/app/api/process/route.ts:24` - Audio processing orchestration
- `frontend/app/api/upload/route.ts:61` - Supabase Storage upload
- `audio-transcription-pipeline/ui-web/backend/app/services/pipeline_service.py:41` - Transcription pipeline

**Database:**
- `supabase/schema.sql:33` - therapy_sessions table definition
- `supabase/schema.sql:154` - audio-sessions storage bucket

---

## Architecture Diagrams

### Current Data Flow (Audio → Text)

```
User uploads audio
    ↓
frontend/app/api/upload/route.ts
    ↓
Supabase Storage (audio-sessions bucket)
    ↓
frontend/app/api/process/route.ts
    ↓
audio-transcription-pipeline (port 8000)
    ↓
OpenAI Whisper API (transcription)
    ↓
Pyannote (speaker diarization)
    ↓
Speaker alignment + combining
    ↓
GPT-4 (topic/mood extraction)
    ↓
PostgreSQL therapy_sessions table
    ↓
Frontend dashboard display
```

### Planned Audio Generation Flow (Text → Audio)

```
Session JSON transcripts (mock-therapy-data/sessions/)
    ↓
scripts/generate_audio.py
    ↓
For each aligned_segment:
    ├─ SPEAKER_00 → Hume AI (male voice)
    └─ SPEAKER_01 → Hume AI (non-binary voice)
    ↓
Segment MP3 files (temp)
    ↓
ffmpeg combine
    ↓
Session MP3 file (backend/uploads/audio/alex_chen/)
    ↓
scripts/upload_to_supabase.py
    ↓
Supabase Storage (audio-sessions/alex_chen/)
    ↓
Update therapy_sessions.audio_file_url
    ↓
Frontend can play audio in session detail view
```

---

## Key Decisions

**1. Audio Generation Service: Hume AI Octave**
- **Rationale**: Already specified in documentation, supports non-binary voices
- **Alternative**: ElevenLabs (higher quality but more expensive)

**2. Voice Selection:**
- Therapist: Male voice (matches Dr. Sarah Mitchell character)
- Patient: Non-binary/androgynous voice (matches Alex Chen's identity)

**3. Segment-Level Generation:**
- Generate audio per aligned_segment (not combined segments)
- Provides finer control over timing and pauses
- Easier to debug individual segments

**4. Frontend Integration: Hybrid Approach**
- Keep existing mock data for reference
- Add real sessions alongside
- Allows A/B comparison during testing

**5. File Storage:**
- Generate locally first (backend/uploads/audio/)
- Upload to Supabase Storage after validation
- Maintains local backup for development

---

## Open Questions

**1. Hume AI API Costs:**
- Need to confirm pricing per character/minute
- 12 sessions × 50 minutes avg = 10.25 hours of audio
- Estimate cost before batch generation

**2. Voice Selection Process:**
- How to audition Hume AI voices before selection?
- Should we generate test samples for voice quality review?

**3. Audio Quality Requirements:**
- What bitrate/sample rate for production use?
- File size constraints for Supabase Storage?

**4. Session 12 Fix Approach:**
- Regenerate entire session vs. update metadata?
- Need clarification on preferred clinical arc for final session

**5. Frontend Audio Playback:**
- Does dashboard need audio player component?
- Should transcript auto-scroll with audio playback?
- Waveform visualization requirements?

---

## Risks and Mitigation

**Risk 1: Hume AI API Rate Limits**
- **Impact**: Batch generation may fail or timeout
- **Mitigation**: Implement retry logic, generate in smaller batches (3-4 sessions at a time)

**Risk 2: Audio Quality Issues**
- **Impact**: Voices may sound robotic or unnatural
- **Mitigation**: Test with 1 session first, review quality before batch generation

**Risk 3: Timestamp Alignment Errors**
- **Impact**: Audio may not match transcript timing
- **Mitigation**: Validate duration matches metadata, add silence padding if needed

**Risk 4: Large File Sizes**
- **Impact**: Slow uploads/downloads, storage costs
- **Mitigation**: Compress MP3 to 64kbps (acceptable for voice), estimate 8-12MB per session

**Risk 5: Frontend Performance**
- **Impact**: 22 sessions may slow dashboard rendering
- **Mitigation**: Implement pagination, lazy loading, or virtualization

---

## Related Research

This is the first research document in `thoughts/shared/research/`. Future related research:
- Audio playback component implementation
- Real-time processing status UI optimization
- Supabase Storage cost analysis
- Alternative TTS service evaluation

---

## Conclusion

**Summary:**
The codebase has comprehensive data preparation (12 session transcripts validated) and frontend infrastructure (dashboard-v3 with upload flow) but lacks the critical audio generation implementation. Hume AI TTS integration is 0% complete and must be built from scratch.

**Immediate Next Step:**
Fix session_12_thriving.json timestamp issue (30 minutes), then implement Hume AI audio generation script (4-8 hours).

**Blocker:**
Cannot proceed with frontend audio integration until MP3 files are generated.

**Recommended Action:**
1. Run session 12 regeneration today
2. Set up Hume AI account and test 1-session generation
3. If quality passes review, batch generate all 12 sessions
4. Upload to Supabase Storage
5. Integrate into frontend dashboard-v3

**Target Completion:** 1-2 days for full pipeline (assuming Hume AI setup is straightforward)
