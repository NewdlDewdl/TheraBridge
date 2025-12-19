# Dashboard Prototypes (v2)

**Purpose:** Early-stage dashboard design exploration for TherapyBridge patient/therapist progress tracking.

## View the Mockups

**Route:** `/patient/dashboard-v2`

Run the frontend dev server and navigate to this route to compare both dashboard designs side-by-side.

```bash
cd frontend
npm run dev
# Open http://localhost:3000/patient/dashboard-v2
```

---

## Design Approaches

### Mockup 1: "Serene Analytics"
**File:** `mockup-1-serene.tsx`

**Design Philosophy:**
- Refined minimalism with generous spacing
- Soft gradients and ethereal backgrounds
- Clinical data presented with warmth
- Editorial serif headings + clean sans body text

**Color Palette (therapy-appropriate):**
- Primary: Soft teal (#5AB9B4) - calming, trust, growth
- Secondary: Warm lavender (#B8A5D6) - comfort, healing
- Accent: Gentle coral (#F4A69D) - warmth, encouragement
- Neutral: Warm gray (#F7F5F3) - safety, softness

**Typography:**
- Headings: Crimson Pro (serif, editorial feel)
- Body: Inter (clean, readable)

**Layout Strategy:**
- Top: 2-column clinical progress card + homework completion stat
- Middle: Vertical timeline with milestone markers
- Bottom: Active homework list
- Space-efficient but not cramped
- Strong visual hierarchy

**Best for:** Users who prefer clean, uncluttered interfaces with clear data visualization

---

### Mockup 2: "Warm Grid"
**File:** `mockup-2-warm-grid.tsx`

**Design Philosophy:**
- Masonry-style grid with organic card sizes
- Warmer, more approachable color palette
- Compact but friendly spacing
- Rounded typography for warmth

**Color Palette (therapy-appropriate):**
- Primary: Warm peach (#FFB499) - comfort, warmth
- Secondary: Sage green (#A8C69F) - healing, growth
- Accent: Soft blue (#8FB8DE) - calm, trust
- Neutral: Cream (#FAF8F5) - warmth, safety

**Typography:**
- Headings & Body: DM Sans (rounded, friendly)
- Data/Numbers: Space Mono (geometric, monospaced)

**Layout Strategy:**
- Responsive grid (1-4 columns based on screen size)
- Clinical progress cards span 2 columns each
- Session cards as individual tiles (natural wrapping)
- Timeline at bottom as horizontal summary
- Maximizes information density without feeling cramped

**Best for:** Users who want to see more information at a glance and prefer warmer, less clinical aesthetics

---

## Dashboard Components (Both Mockups)

### 1. Clinical Progress Tracking
**PHQ-9 (Depression) & GAD-7 (Anxiety)**
- Current scores (large numbers with visual hierarchy)
- Trend indicators (% improvement, up/down arrows)
- Mini bar charts showing 10-session progression
- Color-coded by screening type
- Combines standardized clinical measures with visual feedback

### 2. Homework Completion Rate
- Percentage displayed prominently
- Progress bar with gradient animation
- Count of completed vs. total tasks
- Color-coded for quick assessment

### 3. Session Timeline
**Vertical timeline (Mockup 1) vs. Compact horizontal (Mockup 2)**
- Chronological session list with visual dots
- Color-coded by mood (positive = green, neutral = blue, low = rose)
- Milestone markers (⭐ for breakthroughs, new strategies, clinical improvements)
- Each session shows:
  - Date + Duration
  - Topics discussed (condensed)
  - Strategy introduced/practiced
  - Action items (first 2 shown)

**Auto-detected milestones:**
- New therapeutic strategy introduced
- Significant PHQ-9/GAD-7 score improvement (e.g., "Depression improved 30%")
- Major life events mentioned in transcripts
- Breakthrough moments (AI-detected from keywords)
- Treatment plan milestones

### 4. Active Homework
- All current action items in one list
- Checkbox for completion (visual only for now)
- Completed items shown with strikethrough
- No grouping (simple flat list)

### 5. Session Cards (Grid view - Mockup 2 only)
**Collapsed preview format (max 20 words):**
- Date + Duration
- Mood emoji (😊 positive, 😐 neutral, 😔 low)
- Topics discussed
- Strategy introduced
- First 2 action items (as pills/badges)
- Milestone badge if applicable

**Card interactions:**
- Hover effects (scale up, shadow)
- Clickable (routes to full session detail page)
- Color-coded borders by mood
- Top accent bar appears on hover

---

## Data Structure (Mock Data)

### Clinical Screenings
```typescript
{
  session: number,    // 1-10
  score: number,      // PHQ-9: 0-27, GAD-7: 0-21
  date: string        // "2025-12-17"
}
```

### Sessions
```typescript
{
  id: number,
  date: string,          // "Dec 17" (short format)
  duration: string,      // "50 min" or "50m"
  mood: 'positive' | 'neutral' | 'low',
  topics: string,        // Condensed, <30 chars
  strategy: string,      // Primary technique used
  actions: string[],     // Action items assigned
  milestone?: string     // Optional milestone text
}
```

### Homework
```typescript
{
  text: string,
  completed: boolean,
  sessionId?: number    // Optional for tracking
}
```

---

## Design Decisions

### Session Cards: Why No Labels?
With 10+ session cards on screen, repeating labels like "Mood:", "Topics:", "Strategy:", "Actions:" creates visual clutter. Instead:
- **Layout and icons communicate meaning** (emoji = mood, first line = topics, colored text = strategy, pills = actions)
- **Consistent card structure** allows users to learn the pattern once
- **Cleaner, more scannable** when viewing many cards at once

### Colors: Therapy-Appropriate Palette
- **Avoid clinical sterile whites** (can feel cold, impersonal)
- **Avoid aggressive bright colors** (red, bright yellow - can trigger anxiety)
- **Use calming, trust-building hues:**
  - Teals/blues: calm, trust, stability
  - Soft greens: healing, growth, nature
  - Warm neutrals: safety, comfort, warmth
  - Lavenders/purples: peace, healing, introspection
  - Gentle corals/peaches: encouragement, warmth (not aggressive)

### Why Both Approaches?
- **Serene Analytics:** Better for users who want calm, clinical clarity
- **Warm Grid:** Better for users who want approachable, friendly, information-rich
- **Combining elements:** Final design may take timeline from #1, grid from #2, colors from either

---

## Next Steps

1. **Review mockups** and provide feedback
2. **Choose preferred approach** or identify elements to combine
3. **Refine color palette** based on brand guidelines
4. **Implement backend integration:**
   - Connect to `/api/v1/sessions` endpoint
   - Fetch real PHQ-9/GAD-7 scores
   - Load patient-specific homework
5. **Build full session detail page** (clicked from session cards)
6. **Differentiate therapist vs. patient views:**
   - Patient: see `patient_summary`, limited clinical data
   - Therapist: see `therapist_notes`, full clinical details, edit capabilities

---

## Technical Notes

- Both mockups are **production-ready React components**
- Use **Tailwind CSS** for styling with custom animations
- **Google Fonts** imported (Crimson Pro, Inter, DM Sans, Space Mono)
- **Lucide icons** for consistent iconography
- **Responsive design** (mobile, tablet, desktop)
- **Accessibility:** Color contrast, semantic HTML, keyboard navigation
- **Performance:** CSS-only animations, no heavy libraries

---

## Files

```
dashboard-v2/
├── README.md                    # This file
├── page.tsx                     # Mockup viewer (toggle between designs)
├── mockup-1-serene.tsx          # Serene Analytics design
└── mockup-2-warm-grid.tsx       # Warm Grid design
```

---

**Status:** ✅ Early prototype - ready for review
**Next:** Choose design direction → refine → implement backend integration
