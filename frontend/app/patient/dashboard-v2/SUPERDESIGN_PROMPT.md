# Quick Prompt for SuperDesign

**Copy this entire section and paste into SuperDesign:**

---

Create a therapy progress dashboard for TherapyBridge that tracks 10 therapy sessions. The dashboard should show:

## Data to Display

**1. Clinical Progress (Top Section)**
- PHQ-9 depression scores: Started at 18, now at 6 (67% improvement)
  - Show mini bar chart with 10 data points: 18→16→15→13→12→11→9→8→7→6
  - Large current score display (56px number)
  - Green trend indicator with percentage

- GAD-7 anxiety scores: Started at 15, now at 5 (67% improvement)
  - Show mini bar chart with 10 data points: 15→14→13→12→10→9→8→7→6→5
  - Large current score display (56px number)
  - Green trend indicator with percentage

**2. Homework Completion (Top Section)**
- 50% completion rate
- "3 of 6 tasks completed"
- Visual progress bar with gradient fill

**3. Session Timeline (Middle Section - Vertical Layout)**
Display all 10 sessions in chronological order (oldest at bottom, newest at top):

- Session 10 (Dec 17, 50m): 😊 Positive | Relationship boundaries, self-advocacy | Assertiveness training | Actions: Set boundary, Journal wins

- Session 9 (Dec 10, 45m): 😊 Positive | Self-worth, past relationships | Laddering technique | Actions: Self-compassion practice, Behavioral experiment | ⭐ MILESTONE: "Breakthrough: self-compassion"

- Session 8 (Dec 3, 48m): 😐 Neutral | Work stress, anxiety triggers | 4-7-8 breathing | Actions: Practice breathing 2x daily, Track anxiety

- Session 7 (Nov 26, 45m): 😐 Neutral | Family dynamics, holiday stress | Grounding techniques | Actions: 5-4-3-2-1 during stress, Set boundaries | ⭐ MILESTONE: "New strategy: Grounding"

- Session 6 (Nov 19, 50m): 😔 Low | Loneliness, social isolation | Behavioral activation | Actions: Attend social event, Call friend weekly

- Session 5 (Nov 12, 45m): 😐 Neutral | Sleep issues, rumination | Sleep hygiene plan | Actions: No screens before bed, Journaling | ⭐ MILESTONE: "PHQ-9 improved 30%"

- Session 4 (Nov 5, 50m): 😔 Low | Breakup processing, grief | Emotional validation | Actions: Allow feelings, Support group

- Session 3 (Oct 29, 45m): 😔 Low | Core beliefs exploration | CBT thought records | Actions: Track negative thoughts, Challenge beliefs

- Session 2 (Oct 22, 50m): 😐 Neutral | Therapy goals, treatment plan | Goal setting framework | Actions: Define 3 goals, Track progress | ⭐ MILESTONE: "Treatment plan established"

- Session 1 (Oct 15, 60m): 😐 Neutral | Initial intake, history | Assessment | Actions: Complete intake forms, PHQ-9/GAD-7 baseline | ⭐ MILESTONE: "First session"

**Timeline Visual Requirements:**
- Vertical line connecting all sessions
- Color-coded dots for each session (green = positive, blue = neutral, pink/rose = low)
- Milestone sessions have star badges and stand out visually
- Each session shows: date, duration, mood, topics, strategy, 2 action items max
- No repetitive labels (use layout to communicate meaning)

**4. Active Homework (Bottom Section)**
Simple checklist:
- [ ] Set boundary with friend about time commitments
- [ ] Journal daily wins and moments of self-advocacy
- [x] Practice self-compassion when negative thoughts arise (completed - strikethrough)
- [ ] Conduct behavioral experiment with trusted friend
- [x] Use 4-7-8 breathing when feeling anxious 2x daily (completed - strikethrough)
- [x] Track anxiety triggers in journal (completed - strikethrough)

## Visual Style Requirements

**Color Palette (Therapy-Appropriate):**
Choose ONE of these palettes or create a similar calming palette:

Option 1 - "Serene":
- Primary: Soft teal (#5AB9B4)
- Secondary: Warm lavender (#B8A5D6)
- Accent: Gentle coral (#F4A69D)
- Neutral: Warm gray/cream (#F7F5F3)
- Success: Soft green (#A8C69F)

Option 2 - "Warm":
- Primary: Warm peach (#FFB499)
- Secondary: Sage green (#A8C69F)
- Accent: Soft blue (#8FB8DE)
- Neutral: Cream (#FAF8F5)
- Success: Gentle mint (#B2DFDB)

**IMPORTANT Color Rules:**
- ✅ Use calming colors (teals, blues, greens, warm neutrals)
- ❌ Avoid harsh reds, bright yellows, neon colors
- ❌ Avoid pure white backgrounds (feels cold/clinical)
- ✅ Use gentle gradients for warmth

**Typography:**
- Headings: Serif (like Crimson Pro, Lora) OR rounded sans (like DM Sans, Nunito)
- Body: Clean sans-serif (Inter, Plus Jakarta Sans)
- Numbers/Data: Monospace or geometric (Space Mono, Work Sans)

**Layout:**
- Max width: 1200px (contained, not stretched edge-to-edge)
- Card border radius: 12-16px (soft corners)
- Spacing between sections: 40-48px
- Card padding: 20-24px
- Shadows: Subtle and soft (not harsh drop shadows)

## Design Constraints

**Must Include:**
- All 5 sections (clinical progress, homework rate, timeline, homework list)
- Visual milestone markers (5 sessions have star badges)
- Mood indicators (emojis or colored dots)
- Trend percentages on clinical scores
- Progress bar for homework completion
- Clickable session cards (show hover state)

**Must Avoid:**
- Overwhelming the user with too much text
- Repetitive labels on every card (no "Mood:", "Topics:", "Strategy:" labels)
- Clinical/sterile aesthetic (this should feel warm and encouraging)
- Gamification (no confetti, party emojis, "level up" language)
- Harsh or aggressive colors

**Emotional Tone:**
- Healing, progress-focused, encouraging
- Trustworthy and professional but not corporate
- Calm and supportive (not anxiety-inducing)
- Shows clear journey from struggling (early sessions) to improving (recent sessions)

## Layout Structure

Preferred layout (Analytics Dashboard style):

```
[Page Header: "Your Journey" + "Tracking progress across 10 sessions"]

[Row 1: Clinical Progress Cards]
[PHQ-9 Depression Card - 2 cols] [GAD-7 Anxiety Card - 2 cols]

[Row 2: Homework Stat]
[Homework Completion Card - spans full width or 1/3 width]

[Row 3: Timeline]
[Session Timeline - Vertical, full width, shows all 10 sessions]

[Row 4: Homework List]
[Active Homework - full width, simple checklist]
```

## Success Criteria

A successful design will:
1. Feel calming and encouraging (not anxiety-inducing)
2. Show clear progress from session 1 (struggling) to session 10 (improving)
3. Be scannable (find key info in 5-10 seconds)
4. Make milestones visually prominent (breakthroughs celebrated)
5. Have clear visual hierarchy (clinical scores → timeline → homework)

---

**Additional Context:**
This dashboard is for therapy patients tracking their mental health journey across 10+ sessions. Users may be dealing with anxiety/depression, so the design must be gentle, non-overwhelming, and progress-focused. The goal is to help them see how far they've come and stay motivated with their homework between sessions.

Reference the vertical timeline style (like GitHub contributions or project roadmaps) for the session timeline section. Clinical progress should feel like a health dashboard (Apple Health, Fitbit) but warmer and more therapeutic.

---

**End of Prompt** - Paste everything above into SuperDesign
