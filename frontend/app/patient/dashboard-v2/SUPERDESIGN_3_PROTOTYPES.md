# TherapyBridge Dashboard — Generate 3 Prototypes

**Copy everything below and paste into SuperDesign**

---

## Project Brief

Create **3 different visual prototypes** for a therapy progress dashboard. All 3 should follow the same layout structure but explore different visual treatments (colors, typography, spacing, card styles).

**Purpose:** Track therapy progress across 10 sessions, showing clinical improvement, session timeline, and homework completion.

**Users:** Therapy patients and therapists monitoring mental health progress (anxiety/depression treatment).

---

## Data to Display

### Clinical Scores (Top Section)
- **PHQ-9 Depression:** Current score 6 (started at 18) — 67% improvement
  - Show 10-session trend: 18 → 16 → 15 → 13 → 12 → 11 → 9 → 8 → 7 → 6
- **GAD-7 Anxiety:** Current score 5 (started at 15) — 67% improvement
  - Show 10-session trend: 15 → 14 → 13 → 12 → 10 → 9 → 8 → 7 → 6 → 5

### To-Do Card (Combined)
- **Completion Rate:** 50% (3 of 6 tasks completed)
- **Active Tasks:**
  - [ ] Set boundary with friend about time commitments
  - [ ] Journal daily wins and moments of self-advocacy
  - [x] Practice self-compassion when negative thoughts arise
  - [ ] Conduct behavioral experiment with trusted friend
  - [x] Use 4-7-8 breathing when feeling anxious 2x daily
  - [x] Track anxiety triggers in journal

### 10 Therapy Sessions (Session Cards)

**Session 10** — Dec 17 | 50m | 😊 Positive
- Topics: Relationship boundaries, self-advocacy
- Strategy: Assertiveness training
- Actions: Set boundary, Journal wins

**Session 9** — Dec 10 | 45m | 😊 Positive | ⭐ **MILESTONE: Breakthrough (self-compassion)**
- Topics: Self-worth, past relationships
- Strategy: Laddering technique
- Actions: Self-compassion practice, Behavioral experiment

**Session 8** — Dec 3 | 48m | 😐 Neutral
- Topics: Work stress, anxiety triggers
- Strategy: 4-7-8 breathing
- Actions: Practice breathing 2x daily, Track anxiety

**Session 7** — Nov 26 | 45m | 😐 Neutral | ⭐ **MILESTONE: New strategy (Grounding)**
- Topics: Family dynamics, holiday stress
- Strategy: Grounding techniques
- Actions: 5-4-3-2-1 during stress, Set boundaries

**Session 6** — Nov 19 | 50m | 😔 Low
- Topics: Loneliness, social isolation
- Strategy: Behavioral activation
- Actions: Attend social event, Call friend weekly

**Session 5** — Nov 12 | 45m | 😐 Neutral | ⭐ **MILESTONE: PHQ-9 improved 30%**
- Topics: Sleep issues, rumination
- Strategy: Sleep hygiene plan
- Actions: No screens before bed, Journaling

**Session 4** — Nov 5 | 50m | 😔 Low
- Topics: Breakup processing, grief
- Strategy: Emotional validation
- Actions: Allow feelings, Support group

**Session 3** — Oct 29 | 45m | 😔 Low
- Topics: Core beliefs exploration
- Strategy: CBT thought records
- Actions: Track negative thoughts, Challenge beliefs

**Session 2** — Oct 22 | 50m | 😐 Neutral | ⭐ **MILESTONE: Treatment plan established**
- Topics: Therapy goals, treatment plan
- Strategy: Goal setting framework
- Actions: Define 3 goals, Track progress

**Session 1** — Oct 15 | 60m | 😐 Neutral | ⭐ **MILESTONE: First session**
- Topics: Initial intake, history
- Strategy: Assessment
- Actions: Complete intake forms, Baseline screening

---

## Layout Structure (ALL 3 PROTOTYPES MUST USE THIS)

```
┌────────────────────────────────────────────────────────┐
│  Header: "Your Journey" + subtitle                    │
├────────────────────────────┬───────────────────────────┤
│                            │                           │
│  MAIN AREA (75% width)     │  SIDEBAR (25% width)      │
│                            │                           │
│  ┌──────────────────────┐  │  ┌─────────────────────┐  │
│  │ Clinical Cards       │  │  │  Vertical Timeline  │  │
│  │ PHQ-9 | GAD-7        │  │  │                     │  │
│  └──────────────────────┘  │  │  ● Dec 17  😊       │  │
│                            │  │  │ Boundaries        │  │
│  ┌──────────────────────┐  │  │  ⭐ Dec 10  😊      │  │
│  │ To-Do Card           │  │  │  │ Self-worth        │  │
│  │ (merged completion   │  │  │  │ ✨ Breakthrough  │  │
│  │  rate + checklist)   │  │  │  ● Dec 3   😐       │  │
│  └──────────────────────┘  │  │  │ Work stress       │  │
│                            │  │  ⭐ Nov 26  😐       │  │
│  ┌──────────────────────┐  │  │  │ Family dynamics   │  │
│  │ Session Cards Grid   │  │  │  ● Nov 19  😔       │  │
│  │ (2-column masonry)   │  │  │  │ Loneliness        │  │
│  │                      │  │  │  ⭐ Nov 12  😐       │  │
│  │ [Card] [Card]        │  │  │  ...                │  │
│  │ [Card] [Card]        │  │  └─────────────────────┘  │
│  │ [Card] [Card]        │  │                           │
│  └──────────────────────┘  │                           │
│                            │                           │
└────────────────────────────┴───────────────────────────┘
```

**Key Layout Rules:**
- Page max-width: 1400px, centered
- Main content: 75% width (clinical cards, to-do, session cards)
- Sidebar: 25% width (sticky vertical timeline)
- Gap between main/sidebar: 24px
- Responsive: On tablet/mobile, timeline moves below session cards

---

## Session Card Layout (CRITICAL)

Each session card has **two-column internal split**:

```
┌─────────────────────────────────────────────────────┐
│ ⭐ Breakthrough: self-compassion                    │ ← Milestone badge (top border)
├─────────────────────────────────────────────────────┤
│  Dec 10 • 45m • 😊                                  │ ← Date, duration, mood emoji
├──────────────────────┬──────────────────────────────┤
│ SESSION TOPICS       │ SESSION STRATEGY             │
│ (Left 50%)           │ (Right 50%)                  │
│                      │                              │
│ Self-worth           │ 🧠 Laddering technique       │
│ Past relationships   │                              │
│                      │ Actions:                     │
│                      │ • Self-compassion practice   │
│                      │ • Behavioral experiment      │
└──────────────────────┴──────────────────────────────┘
```

**Session Card Requirements:**
- Two-column internal layout: Topics (left) | Strategy (right)
- Milestone badge: On top border edge for milestone sessions (5 total)
- Mood indicator: Emoji in metadata row
- Color-coded border: Green (positive), Blue (neutral), Rose (low)
- Hover state: Lift effect + shadow increase
- No repetitive labels (layout communicates meaning)

---

## Vertical Timeline (Sidebar)

**Format:**
- Vertical list with connecting line down the left
- Each entry: Colored dot + Date + Mood emoji + Topic summary
- Milestone entries: Star icon instead of dot + milestone text
- Sticky positioning (stays visible while scrolling)

**Example:**
```
● Dec 17  😊  Boundaries
│
⭐ Dec 10  😊  Self-worth
│ ✨ Breakthrough: self-compassion
│
● Dec 3   😐  Work stress
│
⭐ Nov 26  😐  Family dynamics
│ ✨ New strategy: Grounding
```

---

## To-Do Card Structure

**Merge these into ONE card:**
1. Completion rate (50% with progress bar)
2. Active homework checklist (6 items, 3 completed)

**Layout:**
```
┌────────────────────────────────────┐
│  TO-DO                      50% ●●●○○○  │
├────────────────────────────────────┤
│  ████████████░░░░░░░░░░░░  │ ← Progress bar
│  3 of 6 completed               │
│                                 │
│  ○ Set boundary with friend     │
│  ○ Journal daily wins           │
│  ● Self-compassion practice     │ ← Completed (filled circle + strikethrough)
│  ○ Behavioral experiment        │
│  ● 4-7-8 breathing 2x daily     │
│  ● Track anxiety triggers       │
└────────────────────────────────────┘
```

---

## Design Constraints (Apply to All 3 Prototypes)

### Must Use
✅ **Layout:** 75% main content + 25% sidebar timeline
✅ **Session cards:** Two-column split (topics | strategy)
✅ **Milestone badges:** On top border of 5 milestone cards
✅ **To-Do card:** Merged completion rate + checklist
✅ **Typography baseline:**
  - Headings: Serif (Crimson Pro) or rounded sans (DM Sans)
  - Body: Clean sans (Inter or Plus Jakarta Sans)
  - Numbers: Geometric or monospace

✅ **Color palette baseline (Serene):**
  - Primary: Soft teal (#5AB9B4)
  - Secondary: Warm lavender (#B8A5D6)
  - Accent: Gentle coral (#F4A69D)
  - Background: Warm cream (#F7F5F3)

✅ **Mood colors:**
  - Positive: Green spectrum
  - Neutral: Blue/lavender spectrum
  - Low: Rose/pink spectrum (NOT harsh red)

### Must Avoid
❌ Harsh colors (bright red, neon yellow)
❌ Clinical sterile white backgrounds
❌ Separate homework cards (must be merged)
❌ Timeline in main content area (must be in sidebar)
❌ Repetitive labels on every card element
❌ Full-width layouts without container max-width

---

## Generate 3 Variations

Create **3 different visual prototypes** exploring:

### Prototype 1: "Refined Serene"
- Use the Serene color palette (teal, lavender, coral, cream)
- Serif headings (Crimson Pro)
- Generous spacing, soft shadows
- Glassmorphic cards (frosted glass effect)
- Subtle gradients on progress bars and charts

### Prototype 2: "Warm & Friendly"
- Warmer palette: Peach (#FFB499), sage green (#A8C69F), soft blue (#8FB8DE)
- Rounded sans headings (DM Sans, Nunito, Poppins)
- Tighter spacing, more compact
- Flat cards with colored borders
- Solid color fills instead of gradients

### Prototype 3: "Modern Clinical"
- Cooler palette: Deep teal (#2C7A7B), muted purple (#6B46C1), neutral grays
- Geometric sans headings (Inter, Work Sans)
- Medium spacing, crisp edges
- Cards with subtle elevation shadows
- Data-focused (larger charts, smaller text)

**All 3 must:**
- Follow the exact layout structure (75/25 split)
- Use two-column session cards
- Include milestone badges on top border
- Show vertical timeline in sidebar
- Merge homework into one To-Do card
- Feel calm and therapy-appropriate (not overwhelming)

---

## Success Criteria

✅ User sees clear progress from Session 1 (struggling) to Session 10 (improving)
✅ Milestones visually stand out (breakthroughs celebrated)
✅ Timeline provides quick navigation
✅ To-Do card shows homework status at a glance
✅ Session cards are scannable (20 words max per card)
✅ Design feels calming, warm, encouraging (not clinical or chaotic)

---

**End of Prompt** — Generate 3 prototypes exploring different visual treatments of this layout structure.
