# TherapyBridge Frontend Dashboard - Build Prompt

**Context**: This prompt is for Claude to build a modern, real-time frontend dashboard for TherapyBridge, a therapy session transcription and AI note extraction platform.

---

## Project Overview

TherapyBridge is a therapy session management platform that:
1. **Accepts audio uploads** (MP3, WAV, M4A) of therapy sessions
2. **Transcribes** using OpenAI Whisper API with speaker diarization
3. **Extracts structured clinical notes** using GPT-4o including strategies, triggers, mood, action items, risk flags
4. **Provides dual summaries**: Clinical therapist notes + warm patient-facing summary

**Current State**:
- ✅ Backend FastAPI server running on http://localhost:8000
- ✅ Audio transcription pipeline complete
- ✅ AI extraction with GPT-4o working
- ✅ Database schema deployed (Neon PostgreSQL)
- ❌ Frontend dashboard - **THIS IS WHAT WE'RE BUILDING**

**Reference Documentation**:
- Main project docs: `Project MDs/TherapyBridge.md`
- Backend API docs: http://localhost:8000/docs (Swagger UI)
- Backend README: `backend/README.md`
- Backend testing guide: `backend/TESTING_GUIDE.md`

---

## Technical Requirements

### Tech Stack

**Framework**: Next.js 14 (App Router)
- TypeScript for type safety
- Server components where possible
- Client components for interactivity

**Styling**: Tailwind CSS + shadcn/ui
- Use shadcn/ui components for consistent design
- Responsive mobile-first design
- Dark mode support (optional but nice to have)

**State Management**:
- React hooks (useState, useEffect)
- SWR or TanStack Query for data fetching with polling
- No Redux needed for MVP

**API Communication**:
- Fetch API or Axios
- Base URL: `http://localhost:8000/api`
- CORS already configured on backend

**Key Dependencies**:
```json
{
  "next": "^14.0.0",
  "react": "^18.0.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^3.0.0",
  "swr": "^2.0.0",
  "@radix-ui/react-*": "latest",
  "lucide-react": "latest",
  "date-fns": "^2.0.0"
}
```

### Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Landing/login page
│   ├── therapist/
│   │   ├── layout.tsx          # Therapist dashboard layout
│   │   ├── page.tsx            # Patient list
│   │   ├── patients/[id]/
│   │   │   └── page.tsx        # Patient detail + sessions
│   │   └── sessions/[id]/
│   │       └── page.tsx        # Session detail view
│   └── patient/
│       ├── layout.tsx          # Patient portal layout
│       └── page.tsx            # Patient session history
├── components/
│   ├── ui/                     # shadcn/ui components
│   ├── SessionUploader.tsx     # Drag-drop audio upload
│   ├── SessionCard.tsx         # Session preview card
│   ├── SessionStatusBadge.tsx  # Status indicator
│   ├── ExtractedNotes.tsx      # Notes display component
│   ├── StrategyCard.tsx        # Strategy visualization
│   ├── TriggerCard.tsx         # Trigger visualization
│   ├── ActionItemCard.tsx      # Action item with checkbox
│   ├── MoodIndicator.tsx       # Mood visualization
│   └── TranscriptViewer.tsx    # Transcript with timestamps
├── lib/
│   ├── api.ts                  # API client functions
│   ├── types.ts                # TypeScript types (from backend schemas)
│   └── utils.ts                # Helper functions
├── hooks/
│   ├── useSession.ts           # Session polling hook
│   ├── usePatients.ts          # Patients data hook
│   └── useSessions.ts          # Sessions list hook
├── public/
│   └── uploads/                # Optional: local uploads
├── .env.local
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Core Features to Build

### 1. Therapist Dashboard

#### 1.1 Patient List View (`/therapist`)

**Purpose**: Overview of all patients with quick stats

**Components**:
- Header with "Add Patient" button
- Grid/list of patient cards showing:
  - Patient name
  - Latest session date
  - Total sessions count
  - Unresolved action items count
  - Risk flag indicator (if any recent flags)

**Interactions**:
- Click patient card → Navigate to patient detail
- Search/filter patients by name
- Sort by last session date, name, etc.

**API Endpoint**: `GET /api/patients/`

---

#### 1.2 Patient Detail View (`/therapist/patients/[id]`)

**Purpose**: Complete view of one patient's therapy journey

**Layout**:

```
┌─────────────────────────────────────────────────────┐
│ Patient Header                                      │
│ Name | Email | Phone | Edit Button                 │
├─────────────────────────────────────────────────────┤
│ Quick Stats Row                                     │
│ Total Sessions | Active Strategies | Open Actions  │
├─────────────────────────────────────────────────────┤
│ Upload New Session                                  │
│ [Drag & Drop Audio File Here]                      │
├─────────────────────────────────────────────────────┤
│ Sessions Timeline                                   │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│ │ Session │ │ Session │ │ Session │              │
│ │  Card   │ │  Card   │ │  Card   │              │
│ └─────────┘ └─────────┘ └─────────┘              │
├─────────────────────────────────────────────────────┤
│ Longitudinal Insights (Optional for MVP)            │
│ - Strategy progression chart                        │
│ - Trigger frequency heatmap                         │
│ - Mood trajectory graph                             │
└─────────────────────────────────────────────────────┘
```

**Session Card** should show:
- Date/time
- Duration (MM:SS format)
- Status badge (uploading, transcribing, processed, failed)
- Session mood indicator (emoji or color)
- Quick preview: 2-3 key topics
- "View Details" button

**Upload Component**:
- Drag & drop zone
- File type validation (MP3, WAV, M4A, MP4, MPEG, WEBM, MPGA)
- Progress indicator during upload
- Auto-refresh session list after upload
- Real-time status updates (polling)

**API Endpoints**:
- `GET /api/patients/{id}` - Patient info
- `GET /api/sessions/?patient_id={id}` - Sessions for this patient
- `POST /api/sessions/upload?patient_id={id}` - Upload new session

---

#### 1.3 Session Detail View (`/therapist/sessions/[id]`)

**Purpose**: Full clinical notes for a single session

**Layout**:

```
┌─────────────────────────────────────────────────────┐
│ Session Header                                      │
│ Patient Name | Date | Duration | Status | Mood     │
├─────────────────────────────────────────────────────┤
│ Clinical Summary (Therapist Notes)                  │
│ [150-200 word AI-generated clinical summary]       │
├─────────────────────────────────────────────────────┤
│ Key Topics & Summary                                │
│ • Topic 1  • Topic 2  • Topic 3                    │
│ [2-3 sentence summary]                             │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐           │
│ │ Strategies (2)  │ │ Triggers (1)    │           │
│ │ • Laddering     │ │ • Breakup       │           │
│ │   (practiced)   │ │   (severe)      │           │
│ └─────────────────┘ └─────────────────┘           │
├─────────────────────────────────────────────────────┤
│ Action Items (1)                                    │
│ ☐ Conduct behavioral experiment with friend        │
│   Category: interpersonal                           │
│   Details: Discuss personal problem...              │
├─────────────────────────────────────────────────────┤
│ Mood & Emotional Themes                             │
│ Session Mood: Neutral ●●●○○ (Fluctuating)         │
│ Themes: sadness, anxiety, fear, hope               │
├─────────────────────────────────────────────────────┤
│ Significant Quotes (3)                              │
│ "I don't feel like I will ever find somebody..."   │
│ [Context: Core belief from relationship failures]   │
├─────────────────────────────────────────────────────┤
│ Risk Flags                                          │
│ ⚠️ No risk flags identified                        │
├─────────────────────────────────────────────────────┤
│ Follow-up Topics & Unresolved Concerns              │
│ • Further exploration of core beliefs              │
│ • Long-term impact on relationships                │
├─────────────────────────────────────────────────────┤
│ Full Transcript                                     │
│ [Expandable section with timestamped transcript]    │
│ [00:00:15] Therapist: How have you been...         │
│ [00:00:22] Client: I've been struggling...         │
└─────────────────────────────────────────────────────┘
```

**Key Components**:

1. **Status Badge**: Color-coded based on processing stage
   - `uploading` → Blue pulsing
   - `transcribing` → Yellow with spinner
   - `extracting_notes` → Purple with spinner
   - `processed` → Green checkmark
   - `failed` → Red with error icon

2. **Strategy Cards**: Show name, category, status, context
   - Categories: breathing, cognitive, behavioral, mindfulness, interpersonal
   - Status: introduced, practiced, assigned, reviewed
   - Color-coded by category

3. **Trigger Cards**: Show trigger, severity, context
   - Severity badges: mild (yellow), moderate (orange), severe (red)

4. **Action Items**: Checkbox list
   - Mark complete functionality (future: persist to DB)
   - Category badges

5. **Mood Indicator**: Visual representation
   - very_low → 😢 (dark red)
   - low → 😔 (red)
   - neutral → 😐 (gray)
   - positive → 🙂 (light green)
   - very_positive → 😊 (green)
   - Trajectory arrow: ↗️ improving, ↘️ declining, → stable, ↕️ fluctuating

6. **Risk Flags Section**: Prominent when present
   - Type, evidence, severity
   - Red alert styling
   - Action buttons (contact patient, create crisis plan)

7. **Transcript Viewer**: Collapsible, searchable
   - Timestamps
   - Speaker labels (Therapist/Client)
   - Highlight on hover

**API Endpoints**:
- `GET /api/sessions/{id}` - Full session data
- `GET /api/sessions/{id}/notes` - Just the extracted notes

---

### 2. Patient Portal (Simplified)

#### 2.1 Patient Session History (`/patient`)

**Purpose**: Patient sees their own sessions with supportive summaries

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│ Welcome back, [Patient Name]                        │
├─────────────────────────────────────────────────────┤
│ Your Progress                                       │
│ Sessions: 12 | Current Strategies: 5               │
├─────────────────────────────────────────────────────┤
│ Recent Sessions                                     │
│ ┌─────────────────────────────────────────┐        │
│ │ Dec 10, 2025 - 23 minutes               │        │
│ │ You discussed feeling unlovable after...│        │
│ │ Action: Conduct behavioral experiment   │        │
│ │ [Read Full Summary]                     │        │
│ └─────────────────────────────────────────┘        │
├─────────────────────────────────────────────────────┤
│ Your Active Strategies                              │
│ • Laddering (cognitive)                            │
│ • Behavioral Experiments                           │
├─────────────────────────────────────────────────────┤
│ Action Items                                        │
│ ☐ Conduct behavioral experiment with friend        │
└─────────────────────────────────────────────────────┘
```

**Key Differences from Therapist View**:
- Uses `patient_summary` field (warm, supportive tone)
- No clinical jargon
- No risk flags shown
- Simplified navigation
- Read-only (no editing)

---

## Real-Time Updates & Polling

### Critical Feature: Status Polling

When a session is uploaded, the frontend must poll the backend to show real-time progress:

```typescript
// hooks/useSession.ts
import useSWR from 'swr';

export function useSession(sessionId: string, options?: { refreshInterval?: number }) {
  const { data, error, mutate } = useSWR(
    `/api/sessions/${sessionId}`,
    fetcher,
    {
      refreshInterval: options?.refreshInterval ?? 5000, // Poll every 5 seconds
      revalidateOnFocus: true,
    }
  );

  const isProcessing =
    data?.status === 'uploading' ||
    data?.status === 'transcribing' ||
    data?.status === 'extracting_notes';

  return {
    session: data,
    isLoading: !error && !data,
    isError: error,
    isProcessing,
    refresh: mutate,
  };
}
```

**Polling Strategy**:
1. After upload, start polling immediately
2. Poll every 5 seconds while `status` is not `processed` or `failed`
3. Show progress indicator with current status
4. Stop polling once `processed` or `failed`
5. Show success message when done

**User Experience**:
```
┌─────────────────────────────────────────┐
│ ⏳ Processing Session...               │
│                                         │
│ ✅ Uploaded                            │
│ ✅ Transcribing (2:15 remaining)       │
│ 🔄 Extracting notes...                 │
│ ⏸️  Processing complete                │
│                                         │
│ [View Session Details]                 │
└─────────────────────────────────────────┘
```

---

## TypeScript Types

Based on backend Pydantic schemas, define TypeScript types:

```typescript
// lib/types.ts

export type SessionStatus =
  | 'uploading'
  | 'transcribing'
  | 'transcribed'
  | 'extracting_notes'
  | 'processed'
  | 'failed';

export type SessionMood =
  | 'very_low'
  | 'low'
  | 'neutral'
  | 'positive'
  | 'very_positive';

export type MoodTrajectory =
  | 'improving'
  | 'declining'
  | 'stable'
  | 'fluctuating';

export type StrategyStatus =
  | 'introduced'
  | 'practiced'
  | 'assigned'
  | 'reviewed';

export interface Strategy {
  name: string;
  category: string;
  status: StrategyStatus;
  context: string;
}

export interface Trigger {
  trigger: string;
  context: string;
  severity: 'mild' | 'moderate' | 'severe';
}

export interface ActionItem {
  task: string;
  category: string;
  details: string;
}

export interface SignificantQuote {
  quote: string;
  context: string;
  timestamp_start?: number | null;
}

export interface RiskFlag {
  type: string;
  evidence: string;
  severity: string;
}

export interface ExtractedNotes {
  key_topics: string[];
  topic_summary: string;
  strategies: Strategy[];
  emotional_themes: string[];
  triggers: Trigger[];
  action_items: ActionItem[];
  significant_quotes: SignificantQuote[];
  session_mood: SessionMood;
  mood_trajectory: MoodTrajectory;
  follow_up_topics: string[];
  unresolved_concerns: string[];
  risk_flags: RiskFlag[];
  therapist_notes: string;
  patient_summary: string;
}

export interface Session {
  id: string;
  patient_id: string;
  therapist_id: string;
  session_date: string;
  duration_seconds: number | null;
  audio_filename: string | null;
  audio_url: string | null;
  transcript_text: string | null;
  transcript_segments: any | null;
  extracted_notes: ExtractedNotes | null;
  status: SessionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  therapist_id: string;
  created_at: string;
  updated_at: string;
}
```

---

## API Client

```typescript
// lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json();
}

// Patients
export const getPatients = () => fetchApi<Patient[]>('/api/patients/');
export const getPatient = (id: string) => fetchApi<Patient>(`/api/patients/${id}`);

// Sessions
export const getSessions = (patientId?: string, status?: SessionStatus) => {
  const params = new URLSearchParams();
  if (patientId) params.set('patient_id', patientId);
  if (status) params.set('status', status);
  return fetchApi<Session[]>(`/api/sessions/?${params}`);
};

export const getSession = (id: string) =>
  fetchApi<Session>(`/api/sessions/${id}`);

export const getSessionNotes = (id: string) =>
  fetchApi<ExtractedNotes>(`/api/sessions/${id}/notes`);

export const uploadSession = async (patientId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/upload?patient_id=${patientId}`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json() as Promise<Session>;
};
```

---

## UI/UX Considerations

### Color Scheme

Use semantic colors for consistency:

- **Status Colors**:
  - Uploading: Blue (`bg-blue-100`, `text-blue-800`)
  - Transcribing: Yellow (`bg-yellow-100`, `text-yellow-800`)
  - Extracting: Purple (`bg-purple-100`, `text-purple-800`)
  - Processed: Green (`bg-green-100`, `text-green-800`)
  - Failed: Red (`bg-red-100`, `text-red-800`)

- **Mood Colors**:
  - very_low: `bg-red-600`
  - low: `bg-orange-500`
  - neutral: `bg-gray-400`
  - positive: `bg-green-400`
  - very_positive: `bg-green-600`

- **Severity Colors** (triggers):
  - mild: `bg-yellow-200`
  - moderate: `bg-orange-300`
  - severe: `bg-red-400`

### Accessibility

- Proper ARIA labels for screen readers
- Keyboard navigation support
- Focus states on interactive elements
- Color contrast ratios meet WCAG AA standards
- Alt text for icons

### Responsive Design

- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Stack cards vertically on mobile
- Hamburger menu for navigation on small screens

---

## Implementation Phases

### Phase 1: Setup & Scaffolding (30 min)
1. Create Next.js 14 app with TypeScript
2. Install dependencies (Tailwind, shadcn/ui, SWR)
3. Configure API base URL in `.env.local`
4. Set up project structure (folders, files)
5. Define TypeScript types from backend schemas

### Phase 2: Core Components (2 hours)
1. Build shadcn/ui components:
   - Button, Card, Badge, Input, Select, Dialog
2. Create reusable components:
   - SessionStatusBadge
   - MoodIndicator
   - StrategyCard
   - TriggerCard
   - ActionItemCard
3. Build SessionUploader with drag-and-drop

### Phase 3: Therapist Dashboard (3 hours)
1. Patient list page (`/therapist`)
2. Patient detail page (`/therapist/patients/[id]`)
3. Session detail page (`/therapist/sessions/[id]`)
4. Upload functionality with real-time polling
5. Session status indicators

### Phase 4: Patient Portal (1 hour)
1. Patient session history (`/patient`)
2. Display patient_summary instead of therapist_notes
3. Simplified UI without clinical details

### Phase 5: Polish & Testing (1 hour)
1. Error handling and loading states
2. Empty states (no patients, no sessions)
3. Mobile responsive testing
4. Cross-browser testing

---

## Success Criteria

✅ **Must Have**:
- Upload audio file and see real-time processing status
- View all patients and their sessions
- View complete extracted notes for any session
- Patient portal shows warm summaries
- Mobile responsive
- Error handling for failed uploads/processing

✅ **Nice to Have**:
- Search/filter patients and sessions
- Mark action items as complete
- Download transcript as text
- Dark mode toggle
- Keyboard shortcuts
- Session notes export (PDF)

---

## Testing Checklist

After implementation, verify:

- [ ] Can navigate to patient list
- [ ] Can click patient to see detail page
- [ ] Can upload audio file (drag-drop works)
- [ ] Status badge updates during processing (polling works)
- [ ] Session detail page shows all extracted notes
- [ ] Strategies display with correct categories and statuses
- [ ] Triggers show with severity indicators
- [ ] Action items render as checkboxes
- [ ] Mood indicator matches session mood
- [ ] Risk flags show prominently (if present)
- [ ] Transcript is readable and searchable
- [ ] Patient portal shows patient_summary (not therapist_notes)
- [ ] Mobile layout works (responsive)
- [ ] Error states display properly (network error, 404, etc.)

---

## Example Component: SessionUploader

```typescript
// components/SessionUploader.tsx
'use client';

import { useState, useCallback } from 'react';
import { uploadSession } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface SessionUploaderProps {
  patientId: string;
  onUploadComplete?: (sessionId: string) => void;
}

export function SessionUploader({ patientId, onUploadComplete }: SessionUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const session = await uploadSession(patientId, file);
      onUploadComplete?.(session.id);
      router.push(`/therapist/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, [patientId, onUploadComplete, router]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }, [handleUpload]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center
        transition-colors cursor-pointer
        ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        ${isUploading ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {isUploading ? (
        <p>Uploading...</p>
      ) : (
        <>
          <p className="text-lg font-medium">Drop audio file here</p>
          <p className="text-sm text-gray-500">or click to browse</p>
          <input
            type="file"
            accept=".mp3,.wav,.m4a,.mp4,.mpeg,.webm,.mpga"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            className="hidden"
          />
        </>
      )}
      {error && <p className="text-red-500 mt-2">{error}</p>}
    </div>
  );
}
```

---

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Final Notes

- **Start simple**: Build MVP first, add polish later
- **Use shadcn/ui**: Don't reinvent the wheel for common components
- **Test with real data**: Use the existing test session (UUID: `35fdacd4-4797-47ad-9f72-5e6fd2373fd6`)
- **Focus on UX**: Real-time updates are critical for good experience
- **Mobile matters**: Many therapists use tablets/phones

**Estimated build time**: 6-8 hours for full MVP

**When complete**, you should be able to:
1. Open browser to http://localhost:3000
2. See patient list
3. Click patient → see sessions
4. Upload new audio file
5. Watch it process in real-time
6. View beautiful, comprehensive extracted notes

---

**Ready to build? Let's create an amazing dashboard! 🚀**
