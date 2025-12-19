# TherapyBridge Dashboard - Page Layout Architecture
**Version:** 3.0
**Date:** December 2025
**Purpose:** Complete architectural specification for patient/therapist progress dashboard

---

## Table of Contents
1. [Overview](#overview)
2. [Page Structure](#page-structure)
3. [Component Specifications](#component-specifications)
4. [Expansion States](#expansion-states)
5. [Interaction Patterns](#interaction-patterns)
6. [Visual Design System](#visual-design-system)
7. [Responsive Behavior](#responsive-behavior)

---

## Overview

### Design Philosophy
The dashboard is a **widget-based interface** where each component:
- Acts as a self-contained, interactive widget
- Has both **compact** (overview) and **expanded** (detailed) states
- Uses **progressive disclosure** to prevent information overload
- Maintains therapy-appropriate aesthetics (calm, warm, trustworthy)

### Core Principles
1. **Information Hierarchy:** Most important data visible at a glance in compact state
2. **User Control:** All expansions are user-initiated (no auto-expanding)
3. **Focus Management:** Only one modal/fullscreen at a time
4. **Seamless Transitions:** Spring animations (iPhone-style) for all expansions
5. **Accessibility:** Keyboard navigation, screen reader support, proper ARIA labels

---

## Page Structure

### Grid Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER                                                              │
│  [Home Icon] [Sun Icon] | Dashboard | Ask AI | Upload               │
├───────────────────────────────┬─────────────────────────────────────┤
│                               │                                     │
│  TOP ROW (2 large panels)     │                                     │
│  ┌─────────────────────────┐  │  ┌─────────────────────────────┐   │
│  │  Notes / Goals          │  │  │  AI Chat Integration        │   │
│  │  (50% width)            │  │  │  (50% width)                │   │
│  │  [Expandable]           │  │  │  [Fullscreen on click]      │   │
│  └─────────────────────────┘  │  └─────────────────────────────┘   │
│                               │                                     │
├───────────────────────────────┴─────────────────────────────────────┤
│  MIDDLE ROW (3 equal cards - 33/33/33 split)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │  To-Do       │ │  Progress    │ │  Therapist   │                │
│  │  (Card 1)    │ │  Patterns    │ │  Bridge      │                │
│  │  [Expandable]│ │  (Card 2)    │ │  (Card 3)    │                │
│  │  [Carousel]  │ │  [Expandable]│ │  [Expandable]│                │
│  │              │ │  [Carousel]  │ │              │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                     │
├─────────────────────────────────────────┬───────────────────────────┤
│  BOTTOM ROW (80/20 split)               │                           │
│                                         │                           │
│  SESSION CARDS GRID (80% width)         │  TIMELINE (20% width)     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │  ┌─────────────────────┐ │
│  │Dec │ │Dec │ │Dec │ │Nov │           │  │  ● Dec 17           │ │
│  │ 17 │ │ 10 │ │ 3  │ │ 26 │           │  │  │                  │ │
│  └────┘ └────┘ └────┘ └────┘           │  │  ⭐ Dec 10          │ │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │  │  │  Breakthrough    │ │
│  │Nov │ │Nov │ │Nov │ │Oct │           │  │  │                  │ │
│  │ 19 │ │ 12 │ │ 5  │ │ 29 │           │  │  ● Dec 3            │ │
│  └────┘ └────┘ └────┘ └────┘           │  │  │                  │ │
│                                         │  │  ⭐ Nov 26          │ │
│       ● ○  (Pagination dots)            │  │  │                  │ │
│                                         │  │  [Expandable]       │ │
│  [Fullscreen on click]                  │  │  [Popover style]    │ │
│                                         │  └─────────────────────┘ │
└─────────────────────────────────────────┴───────────────────────────┘
```

### Layout Specifications

**Container:**
- Max-width: `1400px`
- Centered: `margin: 0 auto`
- Padding: `48px` horizontal, `48px` vertical

**Grid Gaps:**
- Between top panels: `24px`
- Between middle cards: `24px`
- Between main content and sidebar: `24px`
- Section spacing (vertical): `40px`

**Proportions:**
- Top row: 50% / 50%
- Middle row: 33.33% / 33.33% / 33.33%
- Bottom row: 80% / 20%

---

## Component Specifications

### 1. Notes / Goals Panel

**Position:** Top left (50% width)

**Purpose:** Display AI-generated insights summarizing patient's therapy journey

#### Compact State
```
┌─────────────────────────────────────────────┐
│  Notes / Goals                              │
├─────────────────────────────────────────────┤
│                                             │
│  Based on 10 sessions, you've:             │
│  • Reduced depression 67%                   │
│  • Mastered 3 coping strategies             │
│  • Core pattern: work stress → conflict     │
│                                             │
│  Current focus: Boundaries, Self-compassion │
│                                             │
│  [Subtle hover effect indicates clickable]  │
│                                             │
└─────────────────────────────────────────────┘
```

**Styling:**
- Background: White with subtle warm tint
- Border-radius: `16px`
- Padding: `24px`
- Shadow: Soft drop shadow (`0 2px 8px rgba(0,0,0,0.08)`)
- Typography:
  - Title: `20px`, Crimson Pro, semibold
  - Body: `14px`, Inter, regular

**Hover State:**
- Transform: `scale(1.01)`
- Shadow: Increase to `0 4px 16px rgba(0,0,0,0.12)`
- Cursor: `pointer`

#### Expanded State (Modal)

**Animation:** Spring pop from card position (iPhone app opening style)

**Modal Layout:**
```
┌─────────────────────────────────────────────────┐
│  Notes / Goals                            [×]   │
├─────────────────────────────────────────────────┤
│  AI-Generated Journey Summary                   │
│                                                 │
│  ▼ Clinical Progress                            │
│  Your depression score improved from 18 to 6    │
│  (67% reduction) over 10 sessions. Your anxiety │
│  improved from 15 to 5 (67% reduction). This    │
│  represents significant clinical improvement... │
│                                                 │
│  ▼ Therapeutic Strategies Learned               │
│  • Laddering technique (Session 9)              │
│  • 4-7-8 breathing (Session 8)                  │
│  • Grounding techniques (Session 7)             │
│  You've shown strong engagement with behavioral │
│  exercises and cognitive restructuring...       │
│                                                 │
│  ▼ Identified Patterns                          │
│  A clear pattern emerged: work stress triggers  │
│  relationship conflict, which leads to negative │
│  self-talk. When you practice self-compassion...│
│                                                 │
│  ▼ Current Treatment Focus                      │
│  Your therapist is helping you develop boundary-│
│  setting skills and strengthen self-worth...    │
│                                                 │
│  ▼ Long-term Goals                              │
│  Continue building resilience through consistent│
│  homework completion and active participation...│
│                                                 │
│  [Scrollable content]                           │
└─────────────────────────────────────────────────┘
```

**Modal Specifications:**
- Size: Variable based on content (max 80% viewport width/height)
- Background: White
- Border-radius: `24px`
- Padding: `32px`
- Shadow: Elevated (`0 20px 60px rgba(0,0,0,0.2)`)
- Backdrop: Grey overlay (`rgba(0,0,0,0.3)`)

**Close Behavior:**
- Click X button (top right)
- Click outside modal on grey background
- ESC key

**Content Structure:**
- Collapsible sections with ▼ indicators
- Read-only (no editing)
- Scrollable if content exceeds viewport

---

### 2. AI Chat Integration (Dobby)

**Position:** Top right (50% width)

**Purpose:** AI chatbot for patient support, therapist communication, and session preparation

#### Compact State
```
┌────────────────────────────────────────────┐
│  [Dobby Logo/Icon - centered, ~60px]      │
│                                            │
│  Chat with Dobby to prepare for sessions, │
│  ask questions, and message your therapist.│
│                                            │
│  ┌───────────────┬───────────────┐        │
│  │ "Why does my  │ "Help me prep │  [< >] │ ← 2 prompts visible
│  │  mood drop    │  to discuss   │        │
│  │  after..."    │  boundaries..." │        │
│  └───────────────┴───────────────┘        │
│  ● ○ ○                                     │ ← 6 total prompts
│                                            │
│  ─────────────────────────────────────     │
│  [Type your message...]             [↑]   │
└────────────────────────────────────────────┘
```

**Styling:**
- Background: Light gradient (soft blue tint)
- Border-radius: `16px`
- Padding: `24px`
- Logo: Dobby character icon/avatar
- Description: `14px`, Inter, regular, gray-600
- Prompts: Pill-shaped buttons, `13px`, medium weight
- Prompt carousel: Horizontal scroll, 2 visible at a time, 6 total
- Chat input: Border with focus state

**Prompt Pagination:**
- Horizontal swipe/scroll
- Dots indicator (6 dots, 2 prompts per page = 3 pages)
- Prompts dynamically generated based on:
  - Recent session topics
  - Incomplete homework
  - Mood changes/patterns
  - Time since last therapist message
  - Important events/milestones
- Ordered by importance (AI-determined)

#### Fullscreen State

**Trigger:** Click anywhere on compact chat panel

**Animation:** Fullscreen expansion with spring animation

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  ← Back                                   [×]   │ ← Top bar
├─────────────────────────────────────────────────┤
│                                                 │
│  [Scroll to top to see description]            │ ← Hidden initially
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  [Chat conversation area]                       │
│                                                 │
│  User: How is my progress?                      │
│                                                 │
│  Dobby: Based on your 10 sessions, you've made  │
│  significant progress! Your depression score... │
│                                                 │
│  [Chat messages appear here]                    │
│                                                 │
│  ═══════════════════════════════════════════   │
│                                                 │
│  💡 Suggested prompts:                          │
│  ┌───────────────┬───────────────┐             │
│  │ "Help me prep │ "What patterns│  [< >]      │
│  │  for session" │  do you see?" │             │
│  └───────────────┴───────────────┘             │
│  ● ○ ○                                          │
│                                                 │
│  ─────────────────────────────────────────      │
│  [Type your message...]               [Send]    │
└─────────────────────────────────────────────────┘
```

**Fullscreen Specifications:**
- Background: Full viewport overlay (not modal, fullscreen app)
- Top bar: Back arrow (left), Close X (right)
- Chat area: Full height, scrollable
- Messages: Standard chat bubbles (user = right aligned, Dobby = left aligned)

**Description Behavior:**
- When fullscreen opens, description is scrolled past (not visible)
- User scrolls up to top → sees expanded description
- Expanded description organized (not paragraph):
  ```
  Meet Dobby - Your Therapy Companion

  What I can help with:
  • Prepare for upcoming sessions
  • Ask mental health questions
  • Save topics to discuss later
  • Message your therapist
  • Reference your session data
  ```

**Prompt Suggestions:**
- Remain visible at bottom during conversation
- Update dynamically as conversation progresses
- Hide after user sends first message? (Design decision: keep visible for now)

**Chat History (Future):**
- Left sidebar with past conversations (like Claude)
- Not implemented yet - just note for future

---

### 3. To-Do Card (Card 1)

**Position:** Middle row, leftmost (33% width)

**Purpose:** Track homework tasks with completion rate and expandable checklist

#### Compact State
```
┌────────────────────────────────────────┐
│  To-Do                          50%    │
│  ████████████░░░░░░░░░░░░  (3/6)      │ ← Progress bar
├────────────────────────────────────────┤
│  ○ Set boundary with friend            │
│  ○ Journal daily wins                  │
│  ● Self-compassion practice            │ ← Completed (strikethrough, faded)
│                                        │
│  [+3 more tasks]                       │ ← Indicator of hidden items
│                                        │
│  ● ○ ○  (Carousel: rotate through     │ ← Future carousel functionality
│          different task views)         │
└────────────────────────────────────────┘
```

**Styling (Unique Widget Style):**
- Background: Flat white (no gradient)
- Border: Sharp corners (`8px` border-radius, not rounded like others)
- Border: Subtle `1px` solid border
- Shadow: Minimal (`0 1px 4px rgba(0,0,0,0.06)`)
- Typography: Inter, regular weight (feels functional/systematic)
- Checkboxes: Custom circular checkboxes (16px, teal fill when checked)
- Progress bar:
  - Height: `8px`
  - Border-radius: `4px`
  - Background: Gray-200
  - Fill: Gradient (teal → purple)
  - No animation on compact state

**Hover State:**
- Subtle lift (`translateY(-2px)`)
- Shadow increase

#### Expanded State (Modal)

**Layout:**
```
┌─────────────────────────────────────────────┐
│  To-Do                                [×]   │
│  ██████████░░░░░░░░  50%  (3 of 6)         │
├─────────────────────────────────────────────┤
│  Active Tasks                               │
│                                             │
│  ○ Set boundary with friend about time      │
│    commitments                              │
│    From: Session 10 (Dec 17)                │ ← Shows source session
│                                             │
│  ○ Journal daily wins and moments of        │
│    self-advocacy                            │
│    From: Session 10 (Dec 17)                │
│                                             │
│  ○ Conduct behavioral experiment with       │
│    trusted friend                           │
│    From: Session 9 (Dec 10)                 │
│                                             │
│  ───────────────────────────────────────    │
│  Completed (moved to bottom, not separated) │
│                                             │
│  ● Practice self-compassion when negative   │
│    thoughts arise                           │
│    From: Session 9 (Dec 10)                 │
│                                             │
│  ● Use 4-7-8 breathing when anxious 2x/day  │
│    From: Session 8 (Dec 3)                  │
│                                             │
│  ● Track anxiety triggers in journal        │
│    From: Session 8 (Dec 3)                  │
│                                             │
│  ───────────────────────────────────────    │
│                                             │
│  [+ Add New Task]                           │ ← Manual task creation
│                                             │
│  [Archive Completed]  [Delete Selected]     │ ← Different actions
└─────────────────────────────────────────────┘
```

**Expanded Features:**
- Shows source session for each task
- No priority indicators (keep simple for now)
- Completed tasks automatically move to bottom (smooth animation)
- Archive vs Delete:
  - **Archive:** Moves task to archive (retrievable later, stored in database)
  - **Delete:** Permanently removes task (cannot be recovered)
- Manual task creation: Opens input field to add custom tasks
- Scrollable if tasks exceed modal height

---

### 4. Progress Patterns Card (Card 2)

**Position:** Middle row, center (33% width)

**Purpose:** Visual data insights showing therapy progress patterns

#### Compact State
```
┌────────────────────────────────────────┐
│  Progress Patterns             ● ○ ○   │ ← Carousel dots
├────────────────────────────────────────┤
│                                        │
│  [Large mood trend line chart]         │
│                                        │
│   📈 +30% improvement                  │
│        (brief text)                    │
│                                        │
│  [Subtle hover effect]                 │
│                                        │
│  ● ○ ○  (Carousel: mood, homework,    │
│          consistency, strategies)      │
└────────────────────────────────────────┘
```

**Styling (Unique Widget Style):**
- Background: Gradient (soft teal to lavender)
- Border-radius: Fully rounded (`16px`)
- Shadow: Elevated (`0 4px 12px rgba(0,0,0,0.1)`)
- Typography: Inter, medium weight (data-focused feel)
- Chart colors: Match gradient theme
- Numbers: Space Mono for monospaced clarity

**Carousel Pages (4 total):**
1. **Mood Trend** - Line chart showing session mood over time
2. **Homework Impact** - Bar chart showing completion vs. mood correlation
3. **Session Consistency** - Calendar heatmap showing session frequency
4. **Strategy Effectiveness** - Which coping strategies correlate with improvement

**Carousel Behavior:**
- Horizontal swipe left/right
- Slide transition
- Manual only (no auto-advance)
- Dots show current page (4 dots)

#### Expanded State (Modal)

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Progress Patterns                    [×]   │
├─────────────────────────────────────────────┤
│  ▼ Mood Trend                               │
│  ┌───────────────────────────────────────┐  │
│  │ [Large mood line chart visualization]│  │
│  │                                       │  │
│  │ [Interactive: hover shows values]    │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Your mood has improved 30% over the last   │
│  month. You show consistent positive trends │
│  on weeks when you complete breathing       │
│  exercises and maintain sleep hygiene. Your │
│  lowest mood was Session 4 (Nov 5) when...  │
│                                             │
│  ▼ Homework Completion Impact               │
│  ┌───────────────────────────────────────┐  │
│  │ [Bar chart: completion % vs mood]     │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Weeks with 80%+ homework completion show   │
│  25% better mood scores. Your highest       │
│  completion was Week 3 (Nov 12-18) with...  │
│                                             │
│  ▼ Session Consistency                      │
│  ┌───────────────────────────────────────┐  │
│  │ [Calendar heatmap showing sessions]   │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  You've maintained consistent weekly        │
│  sessions with an average of 7.2 days...    │
│                                             │
│  ▼ Strategy Effectiveness                   │
│  ┌───────────────────────────────────────┐  │
│  │ [Chart showing strategy usage & mood] │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Grounding techniques show the highest      │
│  correlation with mood improvement...       │
│                                             │
│  [Scrollable - all 4 metrics shown]         │
└─────────────────────────────────────────────┘
```

**Expanded Features:**
- All 4 metrics shown in stacked sections (Option A: vertical scroll)
- Each section has larger chart + detailed text insights
- Charts are interactive (hover for values)
- Collapsible sections with ▼ indicators
- Scrollable content

---

### 5. Therapist Bridge Card (Card 3)

**Position:** Middle row, rightmost (33% width)

**Purpose:** Connection prompts, conversation starters, and session preparation

#### Compact State
```
┌────────────────────────────────────────┐
│  Therapist Bridge                      │
├────────────────────────────────────────┤
│  Next Session Topics                   │
│  • Family boundaries                   │
│                                        │
│  Share Progress                        │
│  • Completed 3-week sleep plan         │
│                                        │
│  Session Prep                          │
│  • Review anxiety journal              │
│                                        │
│  [Subtle hover effect]                 │
└────────────────────────────────────────┘
```

**Styling (Unique Widget Style):**
- Background: Soft gradient with warm tint
- Border-radius: Pill-shaped (`20px`)
- Shadow: Soft glow (`0 2px 16px rgba(91,185,180,0.15)`)
- Typography: Inter, light weight (conversational feel)
- Section headings: Shorter, concise (no emojis)
- Bullet points: Condensed to 1-2 items per section

**No Carousel:** All three sections shown in compact state (stacked)

#### Expanded State (Modal)

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Therapist Bridge                     [×]   │
├─────────────────────────────────────────────┤
│  Conversation Starters                      │
│                                             │
│  Based on your recent sessions, consider    │
│  discussing these topics:                   │
│                                             │
│  • How work stress connects to relationship │
│    patterns - you've mentioned this 3 times │
│    but haven't explored it deeply           │
│                                             │
│  • Family boundary-setting - you completed  │
│    homework around this and might benefit   │
│    from discussing your experience          │
│                                             │
│  • Self-worth patterns emerging from past   │
│    relationships - Session 9 breakthrough   │
│    could be expanded further                │
│                                             │
│  ───────────────────────────────────────    │
│                                             │
│  Share Progress with Therapist              │
│                                             │
│  Your therapist would want to know about:   │
│                                             │
│  • 3-week sleep hygiene completion streak   │
│    (consistent bedtime, no screens)         │
│                                             │
│  • 40% anxiety score reduction this week    │
│    (from 10 to 6 on GAD-7)                  │
│                                             │
│  • Successful boundary-setting with friend  │
│    about time commitments                   │
│                                             │
│  ───────────────────────────────────────    │
│                                             │
│  Session Prep                               │
│                                             │
│  Before your next session on Dec 20:        │
│                                             │
│  • Review anxiety trigger journal entries   │
│    from this week to identify patterns      │
│                                             │
│  • Prepare questions about grounding        │
│    technique application in work settings   │
│                                             │
│  • Bring up incomplete behavioral           │
│    experiment - discuss what held you back  │
│                                             │
│  [Read-only text, no interactive elements]  │
│  [Scrollable content]                       │
└─────────────────────────────────────────────┘
```

**Expanded Features:**
- Read-only text content (NO checkboxes, NO buttons)
- All three sections shown with full detail
- Scrollable if content exceeds modal height
- Pure informational content to review before sessions

---

### 6. Session Cards Grid

**Position:** Bottom row, left side (80% width)

**Purpose:** Display therapy sessions in chronological order with pagination

#### Grid Layout
```
Session Cards Grid (Page 1 of 2)

┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Dec 17 │ │ Dec 10 │ │ Dec 3  │ │ Nov 26 │
│  50m   │ │  45m   │ │  48m   │ │  45m   │
│   😊   │ │   😊   │ │   😐   │ │   😐   │
└────────┘ └────────┘ └────────┘ └────────┘

┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Nov 19 │ │ Nov 12 │ │ Nov 5  │ │ Oct 29 │
│  50m   │ │  45m   │ │  50m   │ │  45m   │
│   😔   │ │   😐   │ │   😔   │ │   😔   │
└────────┘ └────────┘ └────────┘ └────────┘

              ● ○  (Page dots)
```

**Grid Specifications:**
- 4 columns × 2 rows = 8 cards per page
- Gap between cards: `16px`
- Order: **Newest first** (reverse chronological: Dec 17 → Oct 15)
- Total sessions: 10 (Page 1: 8 cards, Page 2: 2 cards)

#### Session Card Layout (Two-Column Internal Split)

```
┌─────────────────────────────────────────────┐
│ ⭐ Breakthrough: Self-compassion            │ ← TOP BORDER (milestone only)
├─────────────────────────────────────────────┤
│  Dec 10  •  45m  •  😊                      │ ← METADATA ROW
├──────────────────────┬──────────────────────┤
│                      │                      │
│  SESSION TOPICS      │  SESSION STRATEGY    │ ← Headers (implicit, not shown)
│  (Left 50%)          │  (Right 50%)         │
│                      │                      │
│  Self-worth          │  Laddering technique │
│  Past relationships  │                      │
│                      │  Actions:            │
│                      │  • Self-compassion   │
│                      │  • Behavioral exp.   │
│                      │                      │
└──────────────────────┴──────────────────────┘
```

**Card Specifications:**
- Size: Variable width (responsive to grid), ~200px height
- Border-radius: `12px`
- Shadow: Soft (`0 2px 8px rgba(0,0,0,0.08)`)
- Hover: Lift effect + shadow increase + subtle top accent bar reveal
- Click: Opens fullscreen session detail page

**Milestone Badge (Top Border):**
- Position: Absolutely positioned on top edge, breaking the border
- Style: Pill badge with star icon
- Background: Amber/gold (#FEF3C7)
- Text: Amber-900 (#92400E)
- Typography: Small caps, `12px`, medium weight
- Visual prominence: Elevated z-index, subtle glow (`0 0 12px rgba(251,191,36,0.4)`)
- Appears on 5 sessions: S1, S2, S5, S7, S9

**Metadata Row:**
- Format: `[Date] • [Duration] • [Mood Emoji]`
- Date: "Dec 10" (short month + day)
- Duration: "45m" (abbreviated)
- Mood emoji: Custom or standard (😊 positive, 😐 neutral, 😔 low)
- Typography: `13px`, medium weight, gray-600
- Bullet separator: Gray-400

**Two-Column Split:**
- Left column (50%): Session topics (2-3 keywords, comma-separated or line breaks)
- Right column (50%): Strategy name + 2 action items (bullets or pills)
- Internal gap: `12px`
- Typography:
  - Topics: `14px`, regular, gray-700
  - Strategy: `14px`, semibold, teal-600
  - Actions: `13px`, regular, gray-600

**Mood-Based Card Border:**
- Positive (😊): Green-200 border (`1px` left border accent)
- Neutral (😐): Blue-200 border
- Low (😔): Rose-200 border

**Card Total Content:** Max 20 words (condensed preview)

#### Pagination
- Manual navigation only (no auto-advance)
- Swipe gesture support (horizontal left/right)
- Dots indicator: Page 1 = ●○, Page 2 = ○●
- Slide transition (smooth horizontal slide)
- Page 2 layout: 2 cards centered (Option B)

```
Page 2 (centered):

       ┌────────┐ ┌────────┐
       │ Oct 22 │ │ Oct 15 │
       │  50m   │ │  60m   │
       │   😐   │ │   😐   │
       └────────┘ └────────┘

              ○ ●
```

#### Fullscreen Session Detail

**Trigger:** Click any session card

**Animation:** Fullscreen expansion with spring animation

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  ← Back to Dashboard                      [×]   │
│  Session 9 - Dec 10, 2025                       │
│  ⭐ Breakthrough: Self-compassion                │ ← Milestone in header
├──────────────────────┬──────────────────────────┤
│                      │                          │
│  TRANSCRIPT          │  ANALYSIS                │
│  (Left 50%)          │  (Right 50%)             │
│                      │                          │
│  [Diarized transcript│  Topics Discussed        │
│   with speaker labels│  • Self-worth exploration│
│   Therapist/Patient] │  • Past relationships    │
│                      │  • Negative thought      │
│  Therapist:          │    cycles                │
│  How are you feeling │                          │
│  about the breakup   │  Strategy Used           │
│  this week?          │  Laddering technique -   │
│                      │  helped identify core    │
│  Patient:            │  beliefs about self-worth│
│  I've been struggling│                          │
│  with feeling        │  Session Mood            │
│  unlovable. Every    │  Positive - significant  │
│  time I think about  │  breakthrough moment     │
│  relationships...    │                          │
│                      │  Action Items            │
│  [Full scrollable    │  • Practice self-        │
│   transcript]        │    compassion exercise   │
│                      │  • Conduct behavioral    │
│                      │    experiment            │
│                      │                          │
│                      │  Patient Summary         │
│                      │  You made a significant  │
│                      │  breakthrough in under-  │
│                      │  standing your self-worth│
│                      │  We used the laddering...│
│                      │                          │
│                      │  [Scrollable analysis]   │
│                      │                          │
└──────────────────────┴──────────────────────────┘
```

**Fullscreen Specifications:**
- Full viewport overlay
- Top bar: Back arrow (left), Close X (right), session title + milestone
- Two-column split: 50% transcript / 50% analysis
- Transcript: Diarized with speaker labels, scrollable
- Analysis: All extracted notes (topics, strategy, mood, actions, summary)
- No previous/next navigation (for now)
- ESC key to close

---

### 7. Timeline Sidebar

**Position:** Bottom row, right side (20% width)

**Purpose:** Quick navigation showing all sessions chronologically with milestones

#### Compact State (Default)
```
┌─────────────────────┐
│  Timeline           │
├─────────────────────┤
│                     │
│  ● Dec 17           │
│  │  Boundaries      │
│  │                  │
│  ⭐ Dec 10          │
│  │  Self-worth      │
│  │  Breakthrough    │
│  │                  │
│  ● Dec 3            │
│  │  Work stress     │
│  │                  │
│  ⭐ Nov 26          │
│  │  Family          │
│  │  New strategy    │
│  │                  │
│  ● Nov 19           │
│  │  Loneliness      │
│  │                  │
│  ⭐ Nov 12          │
│  │  Sleep issues    │
│  │  PHQ-9 improved  │
│  │                  │
│  [Scrollable]       │
│                     │
└─────────────────────┘
```

**Styling:**
- Background: White with subtle border
- Border-radius: `12px`
- Padding: `16px`
- Sticky positioning (stays visible while scrolling)

**Timeline Visual Elements:**
- Connector line: Vertical gradient line (2px, teal → lavender → coral)
- Timeline dots:
  - Standard sessions: 10px circles, mood-colored (green/blue/rose)
  - Milestone sessions: 14px star icons with glow
- Entry content:
  - Date: `13px`, medium weight
  - Topic: `12px`, regular weight, truncated to 1-2 words
  - Milestone text: `11px`, italic, amber-700
- Vertical spacing: `16px` between entries

**No Emojis:** Use colored dots instead of mood emojis

**Click Behavior:**
- Clicking entry scrolls to corresponding session card in grid
- Hover highlights the entry

#### Expanded State (Popover Style)

**Trigger:** Click any timeline entry

**Animation:** Popover appears next to timeline (not modal, not fullscreen)

**Layout:**
```
[Timeline]        [Popover appears →]
┌──────────┐     ┌──────────────────────────┐
│  ⭐ Dec 10│ ──→ │  Session 9 - Dec 10      │
│    Self  │     │                          │
│    worth │     │  Duration: 45 minutes    │
└──────────┘     │  Mood: Positive          │
                 │                          │
                 │  Topics:                 │
                 │  • Self-worth exploration│
                 │  • Past relationships    │
                 │                          │
                 │  Strategy:               │
                 │  Laddering technique     │
                 │                          │
                 │  Milestone:              │
                 │  Breakthrough in self-   │
                 │  compassion understanding│
                 │                          │
                 │  [View Full Session →]   │
                 └──────────────────────────┘
```

**Popover Specifications:**
- Style: Floating card next to timeline entry
- Size: ~300px wide, auto height
- Background: White
- Border-radius: `12px`
- Shadow: Elevated (`0 8px 24px rgba(0,0,0,0.12)`)
- Arrow/pointer: Connects to timeline entry
- Close: Click outside or click X button

**Unique Visual Style (Different from Modal):**
- Popover (not modal): Doesn't grey out background
- Attached to timeline: Visual connection with arrow
- Compact preview: Not full detail, just summary
- "View Full Session" button: Opens fullscreen session detail

---

## Expansion States

### Expansion Patterns Summary

| Component | Expansion Type | Close Behavior | Animation |
|-----------|---------------|----------------|-----------|
| Notes/Goals | Modal | Click outside / X / ESC | Spring pop |
| AI Chat (Dobby) | Fullscreen | Back arrow / X / ESC | Spring pop |
| To-Do | Modal | Click outside / X / ESC | Spring pop |
| Progress Patterns | Modal | Click outside / X / ESC | Spring pop |
| Therapist Bridge | Modal | Click outside / X / ESC | Spring pop |
| Session Card | Fullscreen | Back arrow / X / ESC | Spring pop |
| Timeline Entry | Popover | Click outside / X | Fade in |

### Modal Specifications

**Standard Modal (Cards 1, 2, 3, 5):**
- Size: Variable based on content (max 80% viewport width/height)
- Background: White
- Border-radius: `24px`
- Padding: `32px`
- Shadow: Elevated (`0 20px 60px rgba(0,0,0,0.2)`)
- Backdrop: Grey overlay (`rgba(0,0,0,0.3)`) - Light opacity
- Z-index: `1000`

**Close Behavior:**
- X button (top right corner, always visible)
- Click on grey backdrop (outside modal)
- ESC key

**Animation:**
- **Opening:** Spring pop from card position (iPhone app style)
  - Initial state: `transform: scale(0.9), opacity: 0`
  - Final state: `transform: scale(1), opacity: 1`
  - Duration: `400ms`
  - Easing: `cubic-bezier(0.34, 1.56, 0.64, 1)` (spring effect)

- **Closing:** Reverse animation
  - Final state: `transform: scale(0.9), opacity: 0`
  - Duration: `300ms`
  - Easing: `ease-out`

**Focus Management:**
- Trap focus within modal (tab cycling)
- Focus on first interactive element when opened
- Restore focus to trigger element when closed

### Fullscreen Specifications

**Fullscreen (AI Chat, Session Cards):**
- Size: Full viewport (`100vw × 100vh`)
- Background: White (no grey backdrop)
- No border-radius (fills screen)
- Top bar: Navigation controls
  - Back arrow (left): Returns to dashboard
  - Close X (right): Closes fullscreen
  - Title/context in center
- Z-index: `2000` (above modals)

**Animation:** Same spring pop as modals but scales to full viewport

### Popover Specifications

**Popover (Timeline):**
- Size: ~300px wide, auto height (fits content)
- Background: White
- Border-radius: `12px`
- Shadow: `0 8px 24px rgba(0,0,0,0.12)`
- Arrow: 8px triangular pointer to timeline entry
- Z-index: `500` (below modals)

**Animation:**
- **Opening:** Fade in + slight scale up
  - Initial: `opacity: 0, transform: scale(0.95)`
  - Final: `opacity: 1, transform: scale(1)`
  - Duration: `200ms`
  - Easing: `ease-out`

**Positioning:** Dynamically positioned to avoid viewport edges

### Multiple Expansion Constraint

**Rule:** Only ONE modal/fullscreen/popover at a time

**Behavior:**
- Opening new expansion closes any existing expansion
- No prompt for unsaved changes (all content is read-only except To-Do checkboxes)
- Smooth transition: Close previous → Open new

---

## Interaction Patterns

### Carousel Behavior

**Applies to:** To-Do (future), Progress Patterns

**Specifications:**
- Direction: Horizontal (left/right)
- Gesture: Swipe or click arrows
- Transition: Slide animation (`300ms ease-in-out`)
- Dots indicator: Shows current position (● = active, ○ = inactive)
- Manual only: No auto-advance
- Loop: No looping (stop at first/last page)

**Progress Patterns Carousel:**
- 4 pages: Mood Trend, Homework Impact, Session Consistency, Strategy Effectiveness
- Dots: ● ○ ○ ○ (Page 1 active)

### Prompt Pagination (AI Chat)

**Specifications:**
- 6 total prompts, 2 visible at a time = 3 pages
- Horizontal scroll/swipe
- Dots: ● ○ ○ (Page 1 active)
- Prompts: Pill-shaped buttons (~120px wide)
- Click prompt: Inserts text into chat input
- Dynamic: Prompts update based on context/importance

### Hover States

**All Cards:**
- Cursor: `pointer`
- Transform: `scale(1.01)` or `translateY(-2px)`
- Shadow: Increase depth
- Transition: `200ms ease-out`

**Session Cards:**
- Additional: Top accent bar reveal (gradient sweep animation)

### Click Targets

**Minimum size:** 44px × 44px (accessibility guideline)

**Interactive Elements:**
- Buttons: `height: 44px, padding: 12px 24px`
- Checkboxes: `16px` with 44px click target
- Close buttons: `32px` icon with 44px click target
- Carousel arrows: `44px × 44px`

### Keyboard Navigation

**Tab Order:**
1. Header navigation
2. Notes/Goals panel
3. AI Chat panel
4. To-Do card
5. Progress Patterns card
6. Therapist Bridge card
7. Session cards (grid order: left-to-right, top-to-bottom)
8. Timeline entries

**Keyboard Shortcuts:**
- `Tab`: Next element
- `Shift+Tab`: Previous element
- `Enter/Space`: Activate button/link
- `ESC`: Close modal/fullscreen/popover
- Arrow keys: Navigate carousel (when focused)

### Loading States

**Initial Page Load:**
- Skeleton screens for all cards (shimmer animation)
- Load order: Top row → Middle row → Bottom row
- Stagger delay: 100ms between rows

**Component Loading:**
- Spinner or skeleton within card
- Disable interactions until loaded

### Error States

**API Errors:**
- Toast notification (top-right corner)
- Error message in card (with retry button)
- Graceful degradation (show cached data if available)

**Empty States:**
- Illustrated empty state with helpful message
- Call-to-action (e.g., "Complete your first session to see insights")

---

## Visual Design System

### Widget Differentiation

Each card has unique styling to feel like a distinct widget:

| Widget | Border Radius | Shadow | Background | Typography |
|--------|---------------|--------|------------|------------|
| **To-Do** | 8px (sharp) | Minimal | Flat white | Inter, regular |
| **Progress Patterns** | 16px (rounded) | Elevated | Gradient (teal→lavender) | Inter, medium |
| **Therapist Bridge** | 20px (pill) | Soft glow | Warm gradient | Inter, light |
| **Notes/Goals** | 16px | Soft | White + warm tint | Crimson Pro headings |
| **AI Chat** | 16px | Medium | Light blue gradient | Inter |
| **Session Cards** | 12px | Soft | White + mood tint | Inter |
| **Timeline** | 12px | Subtle | White | Inter |

### Color Palette (Serene - from M1)

**Primary Colors:**
- Soft Teal: `#5AB9B4` (Primary CTAs, progress indicators)
- Warm Lavender: `#B8A5D6` (Secondary accents, anxiety metrics)
- Gentle Coral: `#F4A69D` (Warnings, low-mood indicators)

**Neutral Colors:**
- Warm Cream: `#F7F5F3` (Page background)
- White: `#FFFFFF` (Card backgrounds)
- Gray-50 to Gray-900: Standard gray scale

**Mood Colors:**
- Positive: Soft Green `#A8C69F` or Teal `#5AB9B4`
- Neutral: Lavender `#B8A5D6` or Soft Blue `#8FB8DE`
- Low: Gentle Rose `#F4A69D` (NOT harsh red)

**Milestone/Accent:**
- Amber-100: `#FEF3C7` (Milestone badge background)
- Amber-900: `#92400E` (Milestone badge text)
- Gold glow: `rgba(251,191,36,0.4)` (Milestone badge shadow)

### Typography

**Font Families:**
- Headings: Crimson Pro (serif) - editorial, warm
- Body: Inter (sans-serif) - clean, readable
- Data/Numbers: Space Mono (monospace) - optional for charts

**Type Scale:**
- Page Title: `48px`, semibold
- Section Headers: `20px`, semibold
- Card Titles: `18px`, medium
- Body Text: `14px`, regular
- Small Text: `12px`, regular
- Large Numbers (scores): `48-56px`, bold

**Font Weights:**
- Light: 300 (Therapist Bridge)
- Regular: 400 (To-Do, body text)
- Medium: 500 (Progress Patterns, headers)
- Semibold: 600 (headings)
- Bold: 700 (large numbers)

### Spacing System

**Base unit:** 4px

**Scale:**
- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 24px
- 2xl: 32px
- 3xl: 48px

**Common Usage:**
- Card padding: 24px (xl)
- Card gap: 24px (xl)
- Section gap: 40px (between top/middle/bottom rows)
- Button padding: 12px 24px (md xl)
- Input padding: 12px 16px (md lg)

### Shadows

**Levels:**
- None: `box-shadow: none`
- Subtle: `0 1px 4px rgba(0,0,0,0.06)`
- Soft: `0 2px 8px rgba(0,0,0,0.08)`
- Medium: `0 4px 12px rgba(0,0,0,0.1)`
- Elevated: `0 8px 24px rgba(0,0,0,0.12)`
- Modal: `0 20px 60px rgba(0,0,0,0.2)`

**Glow (Milestone):**
- Soft glow: `0 0 12px rgba(251,191,36,0.4)`
- Therapist Bridge glow: `0 2px 16px rgba(91,185,180,0.15)`

### Border Radius

**Scale:**
- Sharp: 8px (To-Do)
- Default: 12px (Session cards, Timeline)
- Rounded: 16px (Most cards, modal inner elements)
- Very rounded: 20px (Therapist Bridge - pill shape)
- Modal: 24px (outer modal container)

### Gradients

**Progress Bar:**
- Linear gradient: `90deg, #5AB9B4 0%, #B8A5D6 100%` (teal → lavender)

**Progress Patterns Background:**
- Linear gradient: `135deg, #5AB9B4 0%, #B8A5D6 100%`

**Timeline Connector Line:**
- Vertical gradient: `to bottom, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%` (teal → lavender → coral)

### Transitions

**Standard:**
- Duration: `200-300ms`
- Easing: `ease-out` or `cubic-bezier(0.4, 0, 0.2, 1)`

**Spring (Expansion):**
- Duration: `400ms` (open), `300ms` (close)
- Easing: `cubic-bezier(0.34, 1.56, 0.64, 1)` (spring bounce)

**Properties to Transition:**
- `transform`
- `opacity`
- `box-shadow`
- `background-color`
- `border-color`

---

## Responsive Behavior

### Breakpoints

**Desktop Only (for MVP):**
- Min-width: `1024px`
- Optimized for: `1440px` viewport

**Future Responsive (not implemented yet):**
- Tablet: `768px - 1023px`
- Mobile: `< 768px`

### Desktop Layout (1024px+)

**Current Specification:**
- Container: `1400px` max-width, centered
- All sections maintain proportions as specified
- No layout changes needed

### Future Tablet/Mobile Considerations

**Tablet (768-1023px):**
- Top row: Stack (Notes/Goals above AI Chat)
- Middle row: 3 cards remain side-by-side (tight)
- Bottom row: Session cards 60%, Timeline 40% (adjusted split)

**Mobile (<768px):**
- All sections stack vertically
- Timeline moves below session cards (horizontal scroll or accordion)
- Session cards: 2 columns instead of 4
- Pagination: More pages, fewer cards per page

**Note:** Mobile responsive not implemented for MVP (web app for desktop hackathon demo)

---

## Technical Implementation Notes

### State Management

**Component State:**
- Card expansion states (which card is expanded)
- Carousel positions (which page is active)
- Checkbox states (To-Do completion)
- Chat conversation history

**Global State (Future):**
- User session data
- Therapy sessions data
- AI-generated insights
- Homework tasks

### Data Flow

**API Endpoints (Backend):**
- `GET /api/v1/sessions` - Fetch all sessions
- `GET /api/v1/sessions/{id}` - Fetch session details
- `GET /api/v1/notes-goals` - Fetch AI-generated journey summary
- `GET /api/v1/homework` - Fetch active homework tasks
- `POST /api/v1/homework/{id}/complete` - Mark task complete
- `POST /api/v1/homework/{id}/archive` - Archive task
- `DELETE /api/v1/homework/{id}` - Delete task
- `POST /api/v1/chat` - Send message to Dobby
- `GET /api/v1/chat/prompts` - Fetch dynamic prompt suggestions

**Mock Data (MVP):**
- Use static mock data for all components
- Match API response structure for easy swapping

### Performance Considerations

**Lazy Loading:**
- Session cards: Load visible page only
- Timeline: Load all (small dataset)
- Modal content: Load on expansion

**Animations:**
- Use CSS transforms (GPU-accelerated)
- Avoid animating layout properties (width, height)
- Prefer `transform` and `opacity`

**Accessibility:**
- ARIA labels for all interactive elements
- Focus management for modals/fullscreens
- Screen reader announcements for state changes
- Keyboard navigation support

---

## Component Checklist

### Must Include ✅
- [ ] Notes/Goals panel (compact + expanded modal)
- [ ] AI Chat Integration (compact + fullscreen)
- [ ] To-Do card (compact + expanded modal + carousel)
- [ ] Progress Patterns card (compact + expanded modal + carousel)
- [ ] Therapist Bridge card (compact + expanded modal)
- [ ] Session cards grid (2-column split, pagination, fullscreen detail)
- [ ] Timeline sidebar (compact + popover expansion)
- [ ] Milestone badges on session cards (top border)
- [ ] All expansion animations (spring pop)
- [ ] Hover states on all interactive elements
- [ ] Modal grey background (light opacity)
- [ ] Close behaviors (X, outside click, ESC)
- [ ] Only one modal/fullscreen at a time
- [ ] Responsive breakpoints (desktop for MVP)

### Must Avoid ❌
- [ ] Multiple simultaneous modals/fullscreens
- [ ] Auto-advancing carousels
- [ ] Emojis in Timeline
- [ ] Interactive elements in Therapist Bridge expanded state
- [ ] Session cards without two-column split
- [ ] Clinical progress cards (PHQ-9/GAD-7) - removed from this design
- [ ] Harsh red colors for low mood (use gentle rose)
- [ ] Gamification (confetti, achievements, etc.)

---

## Future Enhancements (Not in MVP)

**Noted for Later:**
- AI Chat: Left sidebar with conversation history (like Claude)
- AI Chat: User can name the chatbot and customize personality
- Timeline: More event types (homework deadlines, therapist messages, mood spikes)
- Session cards: Previous/next navigation in fullscreen
- To-Do: Priority indicators, task categories
- Progress Patterns: Interactive charts (click data points)
- Responsive layouts for tablet and mobile
- Patient vs. Therapist view differentiation
- Real-time updates (WebSocket for new messages)

---

## End of Architecture Document

**Status:** ✅ Complete architectural specification ready for implementation

**Next Steps:**
1. Review and approve architecture
2. Create Mockup 3 component implementing this specification
3. Integrate with mock data
4. Test all expansion states and interactions
5. Iterate based on feedback

---

**Document Version:** 3.0
**Last Updated:** December 2025
**Maintained By:** TherapyBridge Development Team
