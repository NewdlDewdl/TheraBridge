# TherapyBridge - Complete Algorithm Pipeline

**Single Giant Mermaid Flowchart - Copy & Paste Ready**

```mermaid
graph TB
    subgraph "PHASE 1: AUDIO UPLOAD (0-5s)"
        A1[👤 User Uploads Audio<br/>mp3/wav/m4a] --> A2[📤 POST /api/upload]
        A2 --> A3[✅ Validate File Type]
        A3 --> A4[🗂️ Supabase Storage<br/>bucket: audio-sessions]
        A4 --> A5[💾 INSERT therapy_sessions<br/>status: pending<br/>progress: 0]
        A5 --> A6[📋 Return session_id]
    end

    subgraph "PHASE 2: TRANSCRIPTION (5-120s)"
        A6 --> B1[🚀 POST /api/trigger-processing<br/>fire-and-forget]
        B1 --> B2[⚙️ POST /api/process<br/>background task]
        B2 --> B3[📥 Download Audio from Storage]
        B3 --> B4[🔄 UPDATE status=processing<br/>progress: 20]
        B4 --> B5[📡 POST Transcription Backend<br/>localhost:8000/api/transcribe]
        B5 --> B6[🔁 Poll Job Status<br/>every 2s, max 60 attempts]

        B6 --> C1[🎵 STEP 1: Audio Preprocessing<br/>- Trim silence<br/>- Normalize volume<br/>- Convert to 16kHz mono MP3]
        C1 --> C2[🎤 STEP 2: Whisper API<br/>model: whisper-1<br/>Get transcript + timestamps]
        C2 --> C3[👥 STEP 3: Pyannote Diarization<br/>v3.1 pipeline<br/>Identify SPEAKER_00, SPEAKER_01]
        C3 --> C4[🔀 STEP 4: Merge Segments<br/>Align word timestamps<br/>with speaker segments]
        C4 --> C5[🏷️ STEP 5: Speaker Role Detection<br/>Heuristic 1: First speaker = Therapist<br/>Heuristic 2: Speaking ratio 30-40%]
        C5 --> C6[📄 DiarizedSegment Array<br/>speaker, text, start, end]

        C6 --> D1[🤖 GPT-4o Quick Analysis<br/>Extract: mood, topics, summary]
        D1 --> D2[💾 UPDATE therapy_sessions<br/>transcript, summary, mood, topics<br/>status: completed, progress: 100]
    end

    subgraph "PHASE 3: WAVE 1 ANALYSIS - PARALLEL (120-140s)"
        D2 --> E1[🚀 POST /api/sessions/id/analyze-full-pipeline]
        E1 --> E2[🎯 AnalysisOrchestrator<br/>UPDATE analysis_status: wave1_running]

        E2 --> F1[⚡ asyncio.gather - Parallel Execution]

        F1 --> G1[📊 Mood Analysis<br/>GPT-5-nano]
        F1 --> G2[📝 Topic Extraction<br/>GPT-5-mini]
        F1 --> G3[💡 Breakthrough Detection<br/>GPT-4o]

        G1 --> H1[🎭 MoodAnalyzer.analyze_session_mood<br/>1. Filter patient dialogue SPEAKER_01<br/>2. Analyze 10+ dimensions:<br/>   - Emotional language<br/>   - Self-reported state<br/>   - Clinical symptoms<br/>   - Suicidal ideation<br/>   - Hopelessness vs hope<br/>   - Functioning level<br/>   - Engagement<br/>   - Anxiety markers<br/>   - Depression markers<br/>   - Positive indicators<br/>3. Generate mood_score 0.0-10.0<br/>4. Round to nearest 0.5]

        H1 --> H2[💾 UPDATE mood_score,<br/>mood_confidence, mood_rationale,<br/>mood_indicators, emotional_tone]

        G2 --> I1[📋 TopicExtractor.extract_metadata<br/>1. Format full conversation<br/>2. Extract with GPT-5-mini:<br/>   - 1-2 main topics<br/>   - 2 action items<br/>   - 1 therapeutic technique<br/>   - 2-sentence summary<br/>3. Validate technique against library 80+<br/>4. Truncate summary to 150 chars]

        I1 --> I2[💾 UPDATE topics, action_items,<br/>technique, summary,<br/>extraction_confidence]

        G3 --> J1[⭐ BreakthroughDetector.analyze_session<br/>1. Multi-pass pattern detection<br/>2. Types:<br/>   - Cognitive Insight<br/>   - Emotional Processing<br/>   - Behavioral Commitment<br/>   - Relational Shift<br/>3. Select primary breakthrough<br/>4. Extract dialogue excerpt]

        J1 --> J2[💾 UPDATE has_breakthrough,<br/>breakthrough_data,<br/>breakthrough_label]

        H2 --> K1[✅ Wave 1 Complete]
        I2 --> K1
        J2 --> K1

        K1 --> K2[💾 UPDATE analysis_status:<br/>wave1_complete<br/>wave1_completed_at: NOW]
    end

    subgraph "PHASE 4: WAVE 2 ANALYSIS - SEQUENTIAL (140-185s)"
        K2 --> L1[🔄 AnalysisOrchestrator._run_wave2<br/>UPDATE analysis_status: wave2_running]

        L1 --> M1[🧠 DeepAnalyzer.analyze_session<br/>1. Fetch patient last 10 sessions<br/>2. Gather context:<br/>   - Mood history + trends<br/>   - Learned techniques<br/>   - Previous breakthroughs<br/>   - Active treatment goals<br/>3. Build analysis prompt:<br/>   - Current session Wave 1 results<br/>   - Full transcript<br/>   - Patient history summary<br/>4. Call GPT-4o clinical synthesis]

        M1 --> M2[🤖 GPT-4o Deep Analysis<br/>Synthesizes:<br/>- Progress assessment<br/>- Key insights clinical + patient<br/>- Skills/techniques used<br/>- Recommendations for next session<br/>- Risk factors if any<br/>- Strengths observed]

        M2 --> M3[💾 UPDATE deep_analysis,<br/>analysis_confidence,<br/>deep_analyzed_at]

        M3 --> N1[📖 ProseGenerator.generate_prose<br/>Auto-triggered after Deep Analysis<br/>1. Transform to patient-facing prose<br/>2. Target: 500-750 words<br/>3. Non-clinical language<br/>4. Narrative structure:<br/>   - Opening: Session overview<br/>   - Body: Key insights, progress<br/>   - Closing: Next steps, encouragement]

        N1 --> N2[🤖 GPT-4o Prose Generation<br/>Input: deep_analysis JSON<br/>Output: Natural narrative]

        N2 --> N3[✅ Validate Word Count<br/>Count words and paragraphs<br/>Ensure 500-750 range]

        N3 --> N4[💾 UPDATE prose_analysis,<br/>prose_generated_at,<br/>analysis_status: complete]
    end

    subgraph "PHASE 5: FRONTEND DISPLAY (185-187s)"
        N4 --> O1[🌐 Frontend Dashboard Loads]
        O1 --> O2[🔄 useSessions hook<br/>SWR auto-refresh every 30s<br/>if in-progress]
        O2 --> O3[📊 Supabase Query<br/>SELECT * FROM therapy_sessions<br/>WHERE patient_id = userId<br/>ORDER BY session_date DESC<br/>LIMIT 50]

        O3 --> P1[🃏 SessionCard Component<br/>Display: date, summary, mood_score,<br/>topics, technique, breakthrough_label<br/>Visual: color-coded mood, star for milestone]

        O3 --> P2[📈 ProgressPatternsCard<br/>Mood chart last 10 sessions<br/>Trend: improving/stable/declining]

        O3 --> P3[📝 NotesGoalsCard<br/>Action items from recent sessions<br/>Active treatment goals]

        O3 --> P4[✅ ToDoCard<br/>Aggregated action items<br/>from all sessions]

        O3 --> P5[🔍 Session Detail Page<br/>Full transcript viewer<br/>Prose analysis<br/>Metadata display<br/>Breakthrough highlight]
    end

    subgraph "PHASE 6: AI CHAT CONTEXT (187-191s)"
        N4 --> Q1[💬 User Opens Dobby AI Chat]

        Q1 --> R1[🔍 buildChatContext userId<br/>STEP 1: Fetch last 10 sessions<br/>STEP 2: Analyze Mood Trend<br/>   - Recent 1-3: avg mood<br/>   - Older 4-10: avg mood<br/>   - Trend: improving/stable/declining<br/>STEP 3: Extract Learned Techniques<br/>STEP 4: Fetch Active Goals<br/>STEP 5: Calculate Goal Progress %<br/>STEP 6: Extract Therapist Name<br/>STEP 7: Get Recent Insights]

        R1 --> R2[📋 ChatContext Object<br/>moodTrend, learnedTechniques,<br/>activeGoals, therapistName,<br/>recentInsights, sessionSummaries]

        R2 --> S1[📝 formatContextForAI<br/>Generate human-readable string:<br/>- Mood trend with numbers<br/>- Learned coping skills list<br/>- Active goals with progress bars<br/>- Recent session summaries<br/>- Breakthrough highlights]

        S1 --> S2[🤖 buildDobbySystemPrompt<br/>Defines:<br/>- Role: Supportive AI companion<br/>- Medical knowledge scope<br/>- Crisis protocol keywords + resources<br/>- Communication style validation-first<br/>- Boundaries: not a therapist replacement]

        S2 --> T1[💬 User Sends Message]

        T1 --> U1[🚨 detectCrisisIndicators<br/>Scan for keywords:<br/>suicide, kill myself, no point,<br/>end it all, hurt myself]

        U1 --> U2{Crisis<br/>Detected?}

        U2 -->|Yes| U3[⚠️ Inject Crisis Context<br/>- Validate pain with compassion<br/>- Assess immediate safety<br/>- Provide 988 + Crisis Text Line<br/>- Encourage therapist contact<br/>- Flag for therapist review]

        U2 -->|No| U4[✅ Build Normal Context]

        U3 --> V1[📤 Build Messages Array<br/>System: DOBBY_PROMPT + CONTEXT + CRISIS<br/>User: message]
        U4 --> V1

        V1 --> V2[🤖 POST OpenAI Chat API<br/>model: gpt-4o<br/>temperature: 0.7<br/>max_tokens: 1000<br/>stream: true]

        V2 --> V3[📡 Stream Response Chunks<br/>Server-Sent Events SSE<br/>data: content ...<br/>data: done true]

        V3 --> V4[💾 Optional: Save to DB<br/>INSERT INTO chat_messages<br/>conversation_id, user_id,<br/>role, content]

        V4 --> V5[👤 Display Streaming Response<br/>to User in Real-Time]
    end

    subgraph "DATABASE SCHEMA"
        DB1[(therapy_sessions<br/>--------------<br/>id UUID PK<br/>patient_id FK<br/>therapist_id FK<br/>session_date<br/>audio_file_url<br/>processing_status<br/>transcript JSONB<br/>summary TEXT<br/>mood_score NUMERIC<br/>topics TEXT[]<br/>action_items TEXT[]<br/>technique TEXT<br/>has_breakthrough BOOL<br/>breakthrough_data JSONB<br/>deep_analysis JSONB<br/>prose_analysis TEXT<br/>analysis_status TEXT)]

        DB2[(users<br/>--------------<br/>id UUID PK<br/>email TEXT UK<br/>first_name<br/>last_name<br/>role TEXT<br/>is_verified BOOL)]

        DB3[(treatment_goals<br/>--------------<br/>id UUID PK<br/>patient_id FK<br/>title TEXT<br/>progress INT<br/>status TEXT)]

        DB4[(chat_messages<br/>--------------<br/>id UUID PK<br/>conversation_id FK<br/>user_id FK<br/>role TEXT<br/>content TEXT)]

        DB5[(analysis_processing_log<br/>--------------<br/>id UUID PK<br/>session_id FK<br/>wave TEXT<br/>status TEXT<br/>retry_count INT<br/>error_message TEXT)]
    end

    style A1 fill:#ffe1e1,stroke:#cc0000,stroke-width:3px
    style D2 fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style K2 fill:#fff4e1,stroke:#cc8800,stroke-width:3px
    style N4 fill:#e1ffe1,stroke:#00cc00,stroke-width:3px
    style U2 fill:#ffcccc,stroke:#cc0000,stroke-width:3px
    style V5 fill:#ccffcc,stroke:#00cc00,stroke-width:3px

    classDef phaseBox fill:#f9f9f9,stroke:#333,stroke-width:2px
    class A1,A2,A3,A4,A5,A6 phaseBox
```

---

## Quick Stats

- **Total Pipeline Time:** ~3 minutes (0s → 191s)
- **Total Phases:** 6 (Upload, Transcription, Wave 1, Wave 2, Display, Chat)
- **Total Nodes:** 90+ nodes showing complete algorithm flow
- **Parallel Execution:** Wave 1 (3 AI models simultaneously)
- **Sequential Execution:** Wave 2 (Deep → Prose)

## Cost per Session

**Total:** ~$0.42 per therapy session

- Whisper API: $0.30 (50 min avg session)
- GPT-4o Quick: $0.01
- GPT-5-nano Mood: $0.002
- GPT-5-mini Topics: $0.005
- GPT-4o Breakthrough: $0.02
- GPT-4o Deep: $0.03
- GPT-4o Prose: $0.02

## Technology Stack

**Frontend:**
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- SWR (data fetching)

**Backend:**
- FastAPI (Python 3.13)
- Supabase (PostgreSQL + Storage)
- Asyncio (parallel processing)

**AI Models:**
- Whisper API (transcription)
- Pyannote 3.1 (diarization)
- GPT-5-nano (mood analysis)
- GPT-5-mini (topic extraction)
- GPT-4o (breakthrough, deep analysis, prose, chat)

**Infrastructure:**
- Vercel (frontend hosting)
- Neon PostgreSQL (database)
- Vast.ai (GPU transcription - optional)

## Legend

- 🔴 **Red Border (A1)**: Upload Phase - User Input
- 🔵 **Blue Border (D2)**: Transcription Complete
- 🟡 **Yellow Border (K2)**: Wave 1 Analysis Complete
- 🟢 **Green Border (N4)**: Wave 2 Complete / Pipeline Done
- 🔴 **Red Fill (U2)**: Crisis Detection Decision Point
- 🟢 **Green Fill (V5)**: Final Output - AI Chat Response

## How to Use This Flowchart

1. **View on GitHub:** Push to repo - Mermaid renders automatically
2. **VS Code:** Install `bierner.markdown-mermaid` extension, press Cmd+Shift+V
3. **Online:** Copy flowchart code → paste at https://mermaid.live
4. **Export:** Use mermaid.live to export as PNG/SVG for presentations

