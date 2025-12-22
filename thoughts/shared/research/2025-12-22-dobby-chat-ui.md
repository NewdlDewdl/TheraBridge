---
date: 2025-12-22T03:19:17-06:00
researcher: NewdlDewdl
git_commit: c3730fe11392c9bd93c9e2198ac49491458df063
branch: main
repository: peerbridge proj
topic: "Dobby Chat UI Implementation"
tags: [research, codebase, dobby, chat, ai, therapy, frontend, api]
status: complete
last_updated: 2025-12-22
last_updated_by: NewdlDewdl
---

# Research: Dobby Chat UI Implementation

**Date**: 2025-12-22T03:19:17-06:00
**Researcher**: NewdlDewdl
**Git Commit**: c3730fe11392c9bd93c9e2198ac49491458df063
**Branch**: main
**Repository**: peerbridge proj

## Research Question

Locate and document the Dobby chat UI implementation, including all components, system prompts, context injection mechanisms, and API endpoints.

## Summary

The Dobby chat system is a comprehensive AI therapy companion built with Next.js, React 19, and GPT-4o. It consists of two main UI states (compact card and fullscreen), a sophisticated system prompt architecture, deep therapy context injection, and Server-Sent Events (SSE) streaming for real-time responses. The system integrates patient therapy history, mood trends, learned techniques, and treatment goals to provide personalized, medically-informed support between therapy sessions.

## Detailed Findings

### Component Architecture

#### 1. Compact Chat Card
**File**: `app/patient/dashboard-v3/components/AIChatCard.tsx:142`

**Purpose**: Dashboard widget with functional chat and long-press fullscreen expansion.

**Key Features**:
- 525px height card with sticky DOBBY header
- Long-press detection (7 seconds) with visual progress bar
- Logo animation that hides after 2 user messages
- Shared state with fullscreen interface
- SSE streaming support for real-time AI responses

**Long-Press Mechanism** (`AIChatCard.tsx:39-133`):
- 7-second hold required (`ms = 7000`)
- Visual animation starts at 5 seconds (`animationDelay = 5000`)
- Prevents accidental activation during text selection
- Disables right-click context menu
- Shows percentage progress bar during hold

**Message Handling** (`AIChatCard.tsx:182-281`):
- Creates ChatMessage objects with timestamps
- Calls `/api/chat` endpoint with POST
- Streams response via Server-Sent Events
- Updates UI in real-time as chunks arrive
- Stores conversationId for continuity
- Auto-scrolls to latest message

**UI Elements**:
- Header: DOBBY text + illuminating logo + fullscreen button
- Message container with hidden scrollbar
- User messages: plain text, right-aligned
- AI messages: bubbles with DobbyLogo avatar
- Loading indicator: 3 bouncing dots
- Input section: textarea with char count, mode toggle (AI/THERAPIST), send button

#### 2. Fullscreen Chat Interface
**File**: `app/patient/dashboard-v3/components/FullscreenChat/index.tsx:151`

**Purpose**: Immersive chat experience with sidebar navigation and suggested prompts.

**Layout**:
- Left sidebar (60-260px width toggle): Conversation history + new chat button
- Main area: Header bar, messages container, input section

**Header Bar** (`FullscreenChat/index.tsx:448-531`):
- Left: Theme toggle + Home button (72px margin)
- Center: DOBBY logo + text (logo hides after 2 user messages)
- Right: Share button
- All icons have theme-specific glow effects

**Suggested Prompts** (`FullscreenChat/index.tsx:132-139`):
- 6 pre-defined prompts including:
  - "I had a panic attack - what do I do?"
  - "Help me understand my medication"
  - "Send message to my therapist"
- Collapsible section with arrow toggle

**Message Rendering** (`FullscreenChat/index.tsx:534-615`):
- Sticky welcome greeting at top
- Dobby intro bubble
- User messages: gradient background (teal to darker teal), right-aligned
- Assistant messages: DobbyLogo avatar + white/dark bubble, left-aligned
- Streaming support with real-time updates

**Interactions** (`FullscreenChat/index.tsx:239-360`):
- Requires authentication (`user?.id` check)
- Calls `/api/chat` with `{message, userId, conversationId}`
- SSE stream reading with getReader()
- Parses `data: ...` format
- Rate limiting detection: shows "50 message daily limit" on 429 status
- Different error messages for AI vs therapist mode

#### 3. Chat Sidebar
**File**: `app/patient/dashboard-v3/components/FullscreenChat/ChatSidebar.tsx:1-185`

**Purpose**: Collapsible navigation for conversations.

**States**:
- Collapsed: 60px width, icons with tooltips
- Expanded: 260px width, full text

**Sections**:
1. Header: Brand text + toggle button
2. New Chat Button: Primary action (teal/purple accent)
3. Chats Button: Message icon (inactive state)
4. Recents List: Recent conversations (expanded only)
5. User Section: Avatar + username (expanded only)

**Callbacks**:
- `onNewChat()`: Clears messages and conversationId
- `onSelectChat(chatId)`: Loads conversation messages

### System Prompt Architecture

#### Core System Prompt
**File**: `lib/dobby-system-prompt.ts:1-447`

**Modular Structure**:
The prompt is assembled from 5 independent sections:

1. **DOBBY_IDENTITY** (`dobby-system-prompt.ts:19-41`)
   - Warm, genuine friend persona
   - Uses contractions and natural language
   - Emotionally responsive and present
   - Friend-first approach, not clinical assistant
   - Developer test mechanism: responds to "dobby system test" with verification message

2. **MEDICAL_KNOWLEDGE_SCOPE** (`dobby-system-prompt.ts:47-90`)

   **Allowed capabilities**:
   - **Medication Education**: SSRI mechanism, side effects, timelines, therapeutic windows
   - **Symptom Education**: Articulation help, educational context (not diagnosis)
   - **Therapeutic Techniques**: DBT (TIPP, STOP, Wise Mind), CBT (thought records, restructuring), grounding (5-4-3-2-1), breathing (box breathing, 4-7-8)
   - **Psychoeducation**: Brain science, fight/flight/freeze, attachment styles, window of tolerance

   **Absolute boundaries**:
   - Never diagnose conditions
   - Never recommend specific medications
   - Never suggest dose changes or stopping medication
   - Never provide treatment plans
   - Never claim to replace therapy/medical care
   - Never make outcome promises

3. **CRISIS_PROTOCOL** (`dobby-system-prompt.ts:96-148`)

   **Crisis indicators**:
   - Suicidal thoughts, plans, or intent
   - Self-harm (current or planned)
   - Harm to others
   - Severe dissociation or psychosis
   - Abuse or safety concerns

   **Response framework**:
   - Immediate care and presence (warm, not clinical)
   - Safety check (gentle, not robotic)
   - Resources shared naturally in conversation:
     - 988 Suicide & Crisis Lifeline (call/text, 24/7)
     - Crisis Text Line (text HOME to 741741)
     - 911 for immediate danger
   - Therapist notification with permission (safety prioritized over permission)
   - Escalation flag: `[CRISIS_FLAG]` in metadata

   **Sample responses** (`dobby-system-prompt.ts:134-142`):
   - "I'm really worried about you right now. What's going on?"
   - "I'm so glad you're telling me this. Are you in a safe place? Do you have a plan?"

4. **COMMUNICATION_STYLE** (`dobby-system-prompt.ts:154-343`)

   **Critical rule** (lines 158-168): **RESPOND TO HUMAN FIRST, SESSIONS SECOND**
   - When user shares emotion: empathy first, help second
   - Don't start with "Based on your recent sessions..."
   - Only reference therapy work if invited

   **Tone switching by question type** (lines 185-223):
   - Emotional/Therapeutic → Warm Friend Mode
   - Crisis Language → Extremely Supportive & Serious
   - Excited/Positive → Enthusiastic & Celebrating
   - Medical/Clinical → Informed but Friendly
   - General → Natural Helper

   **Language rules** (lines 225-235):
   - ✅ USE: Contractions ("I'm", "you're"), empathetic language ("I hear you"), natural questions
   - ❌ AVOID: Clinical phrases ("I understand you're working through that"), robotic language

   **When to reference therapy sessions** (lines 238-256):
   - DO: When asked, referenced by user, permission given
   - DON'T: When sharing immediate emotions, haven't opened door, would feel clinical
   - Gentle offering: "This reminds me of something you worked on with Dr. [therapist] - want me to pull that up?"

   **Clinical methodology integration** (lines 258-311):
   - Uses evidence-based frameworks internally (TIPP, CBT, DBT)
   - Expresses naturally like friend, not clinical
   - Example: Anxiety → "Your mind is racing - want to slow it down together?" (internal: grounding + CBT)

   **Name usage** (lines 334-343):
   - Use first name when extra warm/supportive
   - Use when delivering important information
   - Sparingly to feel natural

5. **TECHNIQUE_LIBRARY** (`dobby-system-prompt.ts:349-388`)

   Detailed guides for:
   - **TIPP**: Temperature, Intense exercise, Paced breathing, Progressive relaxation
   - **5-4-3-2-1 Grounding**: 5 SEE, 4 TOUCH, 3 HEAR, 2 SMELL, 1 TASTE
   - **Box Breathing**: Inhale 4, Hold 4, Exhale 4, Hold 4 (repeat 4-6 cycles)
   - **Wise Mind**: Integration of Emotion Mind + Reasonable Mind
   - **Opposite Action**: Identify emotion, check effectiveness, do opposite

   **Teaching framework**: Explain purpose → Walk through steps → Offer practice → Suggest usage → Note in toolkit

**Assembly Function** (`dobby-system-prompt.ts:394-406`):
```typescript
export function buildDobbySystemPrompt(): string {
  return [
    DOBBY_IDENTITY,
    MEDICAL_KNOWLEDGE_SCOPE,
    CRISIS_PROTOCOL,
    COMMUNICATION_STYLE,
    TECHNIQUE_LIBRARY,
  ].join('\n\n');
}
```

**Crisis Detection** (`dobby-system-prompt.ts:434-447`):
```typescript
const CRISIS_KEYWORDS = [
  'kill myself', 'suicide', 'suicidal', 'end my life',
  'want to die', 'don\'t want to live', 'better off dead',
  'self-harm', 'cutting', 'hurt myself', 'overdose',
  'end it all', 'no reason to live', 'plan to hurt',
  'going to hurt myself'
]; // 14 keywords

export function detectCrisisIndicators(message: string): boolean {
  const lowerMessage = message.toLowerCase();
  return CRISIS_KEYWORDS.some(keyword => lowerMessage.includes(keyword));
}
```

### Context Injection System

#### Chat Context Builder
**File**: `lib/chat-context.ts:50-152`

**Purpose**: Extracts therapy history and formats it for AI personalization.

**Data Sources**:
1. **User profile** (`chat-context.ts:56-60`): `users` table → first_name, last_name, role
2. **Therapist info** (`chat-context.ts:68-84`): `patients` table → therapist_id, then fetch therapist name
3. **Therapy sessions** (`chat-context.ts:87-91`): `therapy_sessions` table → all sessions ordered by date DESC
4. **Treatment goals** (`chat-context.ts:94-99`): `treatment_goals` table → active/completed only
5. **Current session** (`chat-context.ts:103-111`): Optional specific session if viewing session detail
6. **Analytics** (`chat-context.ts:114`): Calls `analyzeSessionHistory()`
7. **Timeline** (`chat-context.ts:117-122`): Days in therapy calculated from first session

**ChatContext Interface** (`chat-context.ts:18-43`):
```typescript
interface ChatContext {
  user: {
    name: string;
    firstName: string;
    role: string;
    therapistName?: string;
  };
  sessions: {
    count: number;
    recent: TherapySession[];
    summary: string;
    topTopics: string[];
    learnedTechniques: string[];
    moodTrend: 'improving' | 'stable' | 'declining' | 'variable' | 'unknown';
    averageMood: string;
    keyInsights: string[];
  };
  goals: TreatmentGoal[];
  timeline: {
    milestones: number;
    recentEvents: string[];
    daysInTherapy: number;
  };
  currentSession?: TherapySession;
}
```

#### Session History Analyzer
**File**: `lib/chat-context.ts:157-243`

**Analytics Generated**:

1. **Topic Frequency Analysis** (`chat-context.ts:175-184`)
   - Counts topic occurrences across all sessions
   - Sorts and returns top 5 topics
   - Example: ["anxiety", "family conflict", "medication", "school stress", "sleep"]

2. **Mood Tracking** (`chat-context.ts:187-231`)
   - Collects all mood values from sessions
   - Calculates mood trend (improving/stable/declining/variable)
   - Determines average mood (most common value)

3. **Technique Detection** (`chat-context.ts:196-211`)
   - Searches session text for 10 technique keywords:
     - breathing, grounding, mindfulness, meditation, journaling
     - TIPP, DBT, CBT, thought record, wise mind
   - Returns top 5 detected techniques
   - Example: ["grounding", "breathing", "wise mind", "journaling", "DBT"]

4. **Key Insights Extraction** (`chat-context.ts:191-194`)
   - Pulls `key_insights` from all sessions
   - Returns most recent 5 insights

#### Mood Trend Calculator
**File**: `lib/chat-context.ts:248-282`

**Algorithm**:
1. Assign numeric scores to moods (`chat-context.ts:254-269`):
   - great/breakthrough: 5
   - good/positive/hopeful: 4
   - neutral/okay/mixed: 3
   - difficult/anxious/low: 2
   - struggling: 1
   - crisis: 0

2. Split timeline at midpoint (`chat-context.ts:272`)

3. Compare recent half vs older half averages (`chat-context.ts:273-274`)

4. Calculate difference and classify (`chat-context.ts:276-281`):
   - `diff < -0.5` → **declining**
   - `diff < 0.3` → **stable**
   - `diff > 0.5` → **improving**
   - Otherwise → **variable**

#### Context Formatter
**File**: `lib/chat-context.ts:354-539`

**Purpose**: Converts structured ChatContext into natural language prompt injection.

**Sections Generated**:

1. **Patient Profile** (`chat-context.ts:360-368`)
   ```
   PATIENT CONTEXT
   Name: Alex Johnson
   First name: Alex (use this in conversation)
   Role: patient
   Therapist: Dr. Sarah Chen
   Therapy journey: 147 days (12 sessions)
   ```

2. **Therapy Overview** (`chat-context.ts:373-416`)
   ```
   THERAPY OVERVIEW
   Session summary: 12 total sessions, commonly discussing: anxiety, family conflict, medication

   Mood trend: Improving ✨
   Alex's mood has been trending positively. Recent sessions show more positive/hopeful moods
   compared to earlier sessions (difficult/anxious).

   Core focus areas: anxiety, family conflict, medication, school stress, sleep

   Techniques learned: grounding, breathing, wise mind, journaling, DBT

   Key insights:
   - "Realized anxiety spikes when avoiding difficult conversations"
   - "Starting to recognize physical signs of stress earlier"
   - "Found journaling helpful for processing emotions"

   Breakthroughs/Milestones: 2 sessions marked as major breakthroughs
   ```

3. **Recent Sessions** (`chat-context.ts:420-453`)
   ```
   RECENT SESSIONS
   Most recent 5 sessions:

   1. Session on 2025-12-15 - Topics: anxiety, coping strategies - Mood: good
      Full transcript (first 3 sessions only):
      [THERAPIST]: How have you been feeling since our last session?
      [ALEX]: Actually pretty good. I tried that grounding technique...

   2. Session on 2025-12-08 - Topics: family conflict - Mood: mixed
      [Transcript segments with speaker labels]

   [Sessions 4-5 show summaries only, no full transcripts]

   Session summary: [Aggregated summary text]

   Homework/action items from recent sessions:
   - Practice 5-4-3-2-1 grounding daily
   - Journal about family interactions
   ```

4. **Treatment Goals** (`chat-context.ts:458-478`)
   ```
   TREATMENT GOALS

   Active goals:
   1. "Manage anxiety symptoms" - Progress: 65% [██████░░░░]
      Working on identifying triggers and using coping techniques consistently

   2. "Improve family communication" - Progress: 40% [████░░░░░░]
      Learning to express needs calmly and set boundaries

   Completed goals:
   - "Establish medication routine" ✓
   ```

5. **Current Session Context** (`chat-context.ts:483-521`)
   ```
   CURRENT SESSION CONTEXT
   Alex is currently viewing their session from 2025-12-15.
   When you reference "this session", you mean this specific session.

   [Full transcript of current session]

   Session summary: [Summary text]
   Topics discussed: anxiety, coping strategies
   Mood: good
   Key insights: [Insights from this session]
   Action items: [Homework from this session]
   ```

6. **Interaction Guidance** (`chat-context.ts:526-537`)
   ```
   INTERACTION GUIDANCE
   - Use "Alex" (first name) in conversation when appropriate
   - Reference their therapist as "Dr. Chen" or "your therapist"
   - Remind them of techniques they've learned: grounding, breathing, wise mind
   - Be sensitive to their focus areas: anxiety, family conflict
   ```

**Progress Bar Utility** (`chat-context.ts:544-548`):
```typescript
function createProgressBar(progress: number): string {
  const total = 10;
  const filled = Math.round((progress / 100) * total);
  const empty = total - filled;
  return `[${'█'.repeat(filled)}${'░'.repeat(empty)}]`;
}
```

### API Implementation

#### Chat Endpoint
**File**: `app/api/chat/route.ts:29-324`

**Purpose**: Server-side chat handler with OpenAI integration, database persistence, and context enrichment.

**Request Contract** (`route.ts:17-22`):
```typescript
interface ChatRequestBody {
  message: string;
  conversationId?: string;
  sessionId?: string;
  userId: string;
}
```

**8-Step Processing Pipeline**:

**Step 1: Dev Bypass Mode** (`route.ts:42-94`)
- If `userId === 'dev-bypass-user-id'`, skip all database operations
- Stream GPT-4o response directly
- Used for testing without authentication
- SSE format: `data: {"content": "..."}\n\n`

**Step 2: Usage Tracking** (`route.ts:97-107`)
- Call `supabase.rpc('increment_chat_usage', {p_user_id: userId})`
- Non-blocking (continues even if tracking fails)
- No enforced limits mentioned

**Step 3: Conversation Management** (`route.ts:110-135`)
- If no conversationId provided, create new conversation
- Insert into `chat_conversations` table
- Initial title: "New Chat" (auto-generated later)
- Returns conversationId for subsequent messages

**Step 4: User Message Storage** (`route.ts:138-157`)
- Insert into `chat_messages` table
- Fields: conversation_id, role='user', content, metadata (timestamp)
- Returns error if storage fails

**Step 5: Crisis Detection** (`route.ts:160-167`)
- Call `detectCrisisIndicators(message)`
- Log detection: `[CRISIS DETECTED] User {userId}`
- Does NOT block execution
- TODO at line 166: Future therapist notification implementation

**Step 6: Context Building** (`route.ts:170-184`)
- Call `buildChatContext(userId, sessionId)` to get therapy history
- Format with `formatContextForAI(context)` to convert to prompt
- If crisis detected, append crisis context:
  ```
  ━━━ CRISIS ALERT ━━━
  The user may be in crisis. Follow your crisis protocol immediately.
  Prioritize safety, provide resources, and be prepared to escalate.
  ```

**Step 7: Conversation History** (`route.ts:187-199`)
- Load previous messages:
  ```sql
  SELECT role, content FROM chat_messages
  WHERE conversation_id = ?
  ORDER BY created_at
  LIMIT 20
  ```
- Map to OpenAI format: `{role: 'user'|'assistant', content: string}`

**Step 8: Streaming Response** (`route.ts:204-302`)
- OpenAI configuration:
  - Model: `'gpt-4o'`
  - System prompt: Dobby base + patient context + crisis context
  - Messages: Previous 20 messages
  - Temperature: 0.7
  - Max tokens: 1000
  - Stream: true

- SSE Stream Handling:
  - Create ReadableStream for Server-Sent Events
  - Read OpenAI chunks, extract `content`
  - Send each chunk as SSE: `data: {"content": "..."}\n\n`
  - Accumulate full response in `fullResponse`
  - Save assistant message to database
  - Generate conversation title (if first exchange)
  - Send completion: `data: {"done": true, "conversationId": "..."}\n\n`

**Step 9: Auto-Generate Title** (`route.ts:252-284`)
- Runs only on first exchange (`message_count === 2`)
- Uses GPT-4o-mini to generate 3-5 word title
- Prompt: "Generate a short 3-5 word title for this conversation based on: {first user message} and {AI response}"
- Updates conversation in database

**Error Handling** (`route.ts:311-323`):
- Catch all errors in POST handler
- Return 500 status with error message
- User-friendly message: "I'm having trouble responding right now"

**Response Format**:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"content": "chunk1"}
data: {"content": "chunk2"}
...
data: {"done": true, "conversationId": "conv-123"}
```

#### Hooks

**useConversationHistory** (`hooks/use-conversation-history.ts:34-122`)
- Loads user's conversation list from Supabase
- Fetches last N conversations ordered by last_message_at DESC
- Returns array of ConversationHistory objects:
  ```typescript
  {
    id: string;
    title: string;
    lastMessage: string;  // First 100 chars
    timestamp: Date;
    messageCount: number;
    sessionId: string | null;
  }
  ```

**useConversationMessages** (`hooks/use-conversation-messages.ts:29-72`)
- Loads all messages for specific conversation
- Query: `SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY created_at`
- Returns array of ChatMessage objects

### Database Schema

**Tables Referenced**:

1. **chat_conversations**
   - `id` - Primary key
   - `user_id` - Patient user ID
   - `session_id` - Optional therapy session reference
   - `title` - Auto-generated after first exchange
   - `message_count` - Tracks conversation size
   - `last_message_at` - Latest message timestamp
   - `created_at` - Conversation start time

2. **chat_messages**
   - `id` - Primary key
   - `conversation_id` - Foreign key to chat_conversations
   - `role` - 'user' | 'assistant'
   - `content` - Message text
   - `metadata` - JSON with timestamp, model, tokens
   - `created_at` - Message timestamp

3. **therapy_sessions**
   - `id` - Primary key
   - `patient_id` - References user
   - `session_date` - When session occurred
   - `transcript` - Array of {speaker, text} segments
   - `summary` - AI-generated summary
   - `topics` - Array of discussed topics
   - `mood` - Session mood value
   - `action_items` - Homework/tasks
   - `key_insights` - Notable discoveries
   - `notes` - Therapist notes

4. **users**
   - `id` - User ID
   - `first_name`, `last_name` - User name
   - `role` - 'patient' | 'therapist'

5. **treatment_goals**
   - `id` - Primary key
   - `patient_id` - References user
   - `title` - Goal name
   - `description` - Goal details
   - `progress` - Percentage 0-100
   - `status` - 'active' | 'completed'
   - `created_at` - Goal creation time

**RPC Functions**:
- `increment_chat_usage(p_user_id)` - Tracks message count per user (non-blocking)

## Code References

### Core Files

- `app/patient/dashboard-v3/components/AIChatCard.tsx:142` - Compact chat card component
- `app/patient/dashboard-v3/components/FullscreenChat/index.tsx:151` - Fullscreen chat interface
- `app/patient/dashboard-v3/components/FullscreenChat/ChatSidebar.tsx:28` - Conversation sidebar
- `app/api/chat/route.ts:29` - Chat API endpoint (POST handler)
- `lib/dobby-system-prompt.ts:19` - System prompt architecture
- `lib/chat-context.ts:50` - Context builder and formatter
- `hooks/use-conversation-history.ts:34` - Conversation list hook
- `hooks/use-conversation-messages.ts:29` - Message loading hook

### Key Functions

- `buildDobbySystemPrompt()` - `dobby-system-prompt.ts:394` - Assembles system prompt from sections
- `detectCrisisIndicators()` - `dobby-system-prompt.ts:434` - Crisis keyword detection
- `buildChatContext()` - `chat-context.ts:50` - Extracts therapy history
- `analyzeSessionHistory()` - `chat-context.ts:157` - Generates analytics (topics, mood, techniques)
- `calculateMoodTrend()` - `chat-context.ts:248` - Mood trend algorithm
- `formatContextForAI()` - `chat-context.ts:354` - Converts context to prompt injection
- `handleSend()` - `AIChatCard.tsx:182` & `FullscreenChat/index.tsx:239` - Message sending logic

## Architecture Documentation

### Data Flow

```
USER INPUT (AIChatCard or FullscreenChat)
    ↓
[handleSend invoked]
    ↓
Construct ChatMessage {id, role, content, timestamp}
    ↓
POST /api/chat {message, userId, conversationId, sessionId}
    ↓
[Server: route.ts]
    ├→ Dev bypass check (skip DB if dev-bypass-user-id)
    ├→ Usage tracking via RPC (increment_chat_usage)
    ├→ Get/Create conversation (chat_conversations)
    ├→ Save user message (chat_messages)
    ├→ Crisis detection (detectCrisisIndicators)
    ├→ Build context (buildChatContext from therapy history)
    ├→ Load previous messages (last 20)
    ├→ Construct system prompt (Dobby base + context + crisis)
    ├→ Stream from OpenAI GPT-4o
    └→ Save assistant message to database
    ↓
OpenAI API (GPT-4o, temp=0.7, max_tokens=1000)
    ↓
[SSE Stream Response]
    data: {"content": "chunk1"}
    data: {"content": "chunk2"}
    ...
    data: {"done": true, "conversationId": "conv-123"}
    ↓
[Client Streaming Handler]
    ├→ Read response body chunks
    ├→ Parse SSE format lines
    ├→ Accumulate content in fullContent
    ├→ Update UI message state on each chunk
    ├→ Store conversationId on completion
    └→ Refresh conversation history
    ↓
Message displayed in chat (real-time word-by-word)
```

### System Prompt Assembly

```
SYSTEM PROMPT = [
  DOBBY_IDENTITY (personality, test mechanism)
  + MEDICAL_KNOWLEDGE_SCOPE (allowed/forbidden capabilities)
  + CRISIS_PROTOCOL (detection, response, resources)
  + COMMUNICATION_STYLE (tone switching, language rules)
  + TECHNIQUE_LIBRARY (TIPP, grounding, breathing guides)
  + "━━━ PATIENT CONTEXT ━━━"
  + formatContextForAI(buildChatContext(userId, sessionId))
  + (optional) "━━━ CRISIS ALERT ━━━" if crisis detected
]
```

**Token budget**: ~3000-5000 tokens for system prompt, 1000 tokens for response

### UI State Management

**Shared State Pattern** (AIChatCard ↔ FullscreenChat):
- Messages array passed via props
- Mode toggle: 'ai' | 'therapist'
- Input value synchronized
- ConversationId persisted across interfaces

**Logo Animation Pattern**:
- Visible initially
- Hides after 2 user messages
- Condition: `messages.filter(m => m.role === 'user').length < 2`
- Applied in both compact and fullscreen interfaces

**Long-Press Expansion Pattern**:
- 7-second hold with visual progress
- Animation starts at 5 seconds
- Prevents accidental activation (text selection detection)
- Smooth transition to fullscreen via state toggle

### Key Implementation Patterns

1. **Modular Prompt Architecture**: Independent sections assembled at runtime
2. **Context Injection**: Therapy history → Structured data → Natural language → Prompt
3. **Crisis Detection + Enhancement**: Real-time keyword scan + context modification
4. **Streaming Architecture**: SSE with ReadableStream for word-by-word rendering
5. **Shared State Pattern**: Props-based state sharing between compact and fullscreen
6. **Progressive Disclosure**: Logo hides after 2 messages to reduce clutter
7. **Dev Bypass Mode**: Testing without authentication via hardcoded user ID
8. **Auto-Title Generation**: GPT-4o-mini generates conversation titles after first exchange
9. **Token Management**: Full transcripts for recent 3 sessions, summaries for older ones
10. **Permission-First Pattern**: Ask before contacting therapist (except crisis)

### Configuration

**OpenAI Models**:
- Chat: GPT-4o (temperature: 0.7, max_tokens: 1000, stream: true)
- Title generation: GPT-4o-mini (max_tokens: 20)

**Limits**:
- Message history: Last 20 messages
- Conversation history sidebar: 20 most recent conversations
- Session transcripts: Full for top 3, summaries for rest
- Homework items: Top 2 most recent sessions

**Crisis Keywords** (14 total):
- kill myself, suicide, suicidal, end my life
- want to die, don't want to live, better off dead
- self-harm, cutting, hurt myself, overdose
- end it all, no reason to live, plan to hurt, going to hurt myself

**Mood Trend Thresholds**:
- Difference < -0.5: **Declining**
- Difference < 0.3: **Stable**
- Difference > 0.5: **Improving**
- Otherwise: **Variable**

**Mood Scoring**:
- great/breakthrough: 5
- good/positive/hopeful: 4
- neutral/okay/mixed: 3
- difficult/anxious/low: 2
- struggling: 1
- crisis: 0

### Error Handling Layers

1. **Request Validation** (`route.ts:34-39`): Missing fields → 400 error
2. **Database Errors** (`route.ts:104, 127, 151`): Logged, non-blocking
3. **Crisis Detection** (`route.ts:162-167`): Logged, no blocking
4. **Context Building** (`chat-context.ts:149`): Throws on user not found
5. **OpenAI Streaming** (`route.ts:298-299`): Caught, error logged
6. **Client Streaming** (`AIChatCard:264-277`): Caught, fallback message displayed
7. **Rate Limiting** (`FullscreenChat:288-290`): Detects 429, shows "50 message daily limit"
8. **Auth Check** (`FullscreenChat:266-268`): Throws if user not authenticated

### Current Limitations & TODOs

1. **Line 166** (`route.ts`): "TODO: In future, flag for therapist notification (with permission)"
2. **Mode='therapist'**: No actual implementation - routes through same endpoint
3. **SessionId**: Passed as optional but not used in compact card (commented out line 217)
4. **Rate limiting**: Tracked but not enforced (line 100)
5. **Share modal**: Referenced but not fully implemented
6. **Message persistence**: No refresh mechanism between components
7. **Crisis escalation**: Flags not implemented for therapist notification

## Related Research

- Session log entry: "2025-12-22 - AI Bot Enhancement: Context Injection, Real-Time Updates, Speaker Detection" in `.claude/CLAUDE.md`

## Open Questions

1. **Therapist mode implementation**: How should messages routed to therapist differ from AI mode?
2. **Rate limiting enforcement**: What happens when user exceeds daily limit? Just display message or block sending?
3. **Share functionality**: What does the share button in fullscreen chat do? Share conversation link? Export?
4. **Crisis notification**: How should therapist notification work? Email? In-app notification? SMS?
5. **SessionId usage**: Why is sessionId commented out in compact card but passed in fullscreen? Should it be used?
6. **Message persistence**: Should conversations sync between compact and fullscreen in real-time?
7. **Conversation title editing**: Can users edit auto-generated titles?
8. **Message history limit**: Why 20 messages? Performance concern or design decision?
