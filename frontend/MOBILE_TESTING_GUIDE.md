# Mobile Responsiveness Testing Guide

## Quick Reference: Breakpoint Values

Tailwind CSS default breakpoints used in this project:
- `sm`: 640px (landscape phone)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)

## Testing Checklist by Page

### 1. Home Page (`/`)

**What to test:**
- [ ] Hero title: Readable without horizontal scroll
- [ ] Hero subtitle: Not cramped, good line breaks
- [ ] CTA buttons: Stack vertically on mobile, side-by-side on tablet+
- [ ] Feature cards (3 columns): Display as 1 column on mobile, 2 on tablet, 3 on desktop
- [ ] "What's Extracted" card: 2-column list displays as 1 column on mobile
- [ ] Final CTA: Properly centered and clickable

**Mobile (375px):**
- Hero title should be 3-4 lines max
- Buttons should be full-width or centered pair, not squeezed
- Feature cards should be single column with proper spacing

**Tablet (768px):**
- Feature cards should switch to 2-3 columns
- Button layout should adjust

**Desktop (1024px+):**
- Full 3-column grid for features
- All layouts expand properly

---

### 2. Therapist Dashboard (`/therapist`)

**What to test:**
- [ ] "Patients" header and "Add Patient" button: Responsive layout
  - Mobile: Should stack (title above button)
  - Tablet+: Should be side-by-side
- [ ] Patient cards grid: 1 column on mobile, 2 on tablet, 3 on desktop
- [ ] Card content: Stats should be readable
- [ ] Empty state: Proper message and button

**Mobile (375px):**
- Title and button should not squeeze
- Patient cards should be full width with padding
- Patient name should be visible (not truncated)

**Tablet (768px):**
- 2-column grid for patient cards
- Header should align properly

**Desktop (1024px+):**
- 3-column grid for patient cards

---

### 3. Patient Detail (`/therapist/patients/[id]`)

**What to test:**
- [ ] Back button: Accessible on mobile
- [ ] Patient name/details: Readable
  - Mobile: Should be stacked (name, then email, then phone)
  - Tablet+: Can be on same lines if space allows
- [ ] Stats cards: 1 column mobile, 2 tablet, 3 desktop
- [ ] "Upload New Session" heading: Proper spacing
- [ ] Upload component: Should be responsive (see SessionUploader tests)
- [ ] "Sessions Timeline" heading: Proper spacing
- [ ] Session cards grid: 1 column mobile, 2 tablet, 3 desktop

**Mobile (375px):**
- Patient contact info should stack vertically
- Each stat card should be full-width with good padding
- Session cards should be single column

**Tablet (768px):**
- Stats cards: 2 or 3 columns (depending on card width)
- Session cards: 2 columns

---

### 4. Session Detail (`/therapist/sessions/[id]`)

**What to test:**
- [ ] Back button: Easy to tap on mobile
- [ ] Session header card:
  - Mobile: Title and status badge should not squeeze
  - Title and mood indicator should stack
  - Badge should be inline with title or below
- [ ] Processing banner: Full width and readable
- [ ] Clinical Summary: Text readable on mobile
- [ ] Key Topics badges: Wrap properly on mobile (not one line)
- [ ] Strategies & Triggers: 1 column mobile, 2 desktop
- [ ] Action Items: 1 column mobile, 2 desktop
- [ ] Mood & Emotional Themes: Card should be readable
- [ ] Quotes: Border formatting should work
- [ ] Risk Flags: Should have good contrast on mobile
- [ ] Follow-up Topics: List should be readable
- [ ] Transcript Viewer: Should not have horizontal scroll

**Mobile (375px):**
- Session title should wrap nicely
- Each content card should be full-width
- Badges should wrap onto new lines (not squeeze)
- Transcript should be readable without scrolling left-right
- Action item cards should be single column

**Tablet (768px):**
- Strategies & Triggers should be 2 columns
- Action items should be 2 columns

---

### 5. Patient Portal (`/patient`)

**What to test:**
- [ ] Welcome heading: Not too large on mobile
- [ ] Stats cards: 1 column mobile, 2 desktop
  - Stat icon and number: Aligned properly
- [ ] "Active Strategies" card: List should be readable
- [ ] "Action Items" card: Checkboxes should be easy to tap
  - Should have at least 44px height
- [ ] "Recent Sessions" section: Cards should be single column on mobile
  - Session date and mood indicator: Proper layout
  - Summary text: Good line breaks
  - Action items: Should be readable

**Mobile (375px):**
- Stats cards should be full-width
- All content cards should be full-width
- Checkboxes should be at least 44px high (easy to tap)
- Icons should be appropriately sized

**Tablet (768px):**
- Stats cards should be 2 columns
- Session cards remain single column (good for mobile-first design)

---

### 6. Login Page (`/auth/login`)

**What to test:**
- [ ] Form container: Has proper horizontal padding
  - Mobile: Should have padding so form isn't edge-to-edge
  - Should not overflow or scroll horizontally
- [ ] Form width: Constrained to reasonable width on wide screens
- [ ] Email input: Full-width within form, easy to tap
- [ ] Password input: Full-width within form, easy to tap
- [ ] Button: Full-width, at least 44px tall
- [ ] Error message: Readable and not cutoff
- [ ] Links: Easy to tap (at least 44px tall)

**Mobile (375px):**
- Form should have 16px padding on each side minimum
- Inputs should have 44px+ height
- All text should be readable

**Tablet/Desktop:**
- Form should remain centered within viewport
- Width constraint should keep form readable

---

### 7. Signup Page (`/auth/signup`)

**Same tests as Login page, plus:**
- [ ] Role selector dropdown: Opens without overflow
- [ ] All form fields: Properly spaced and readable
- [ ] Error message: Full-width or constrained appropriately

---

### 8. Component-Level Tests

#### SessionCard (`/components/SessionCard.tsx`)
**Test when viewing in a grid:**
- [ ] Date and status badge: Don't squeeze (responsive layout)
- [ ] Mood indicator: Properly positioned
- [ ] Key topics tags: Wrap onto multiple lines if needed
- [ ] Summary text: Good line length on mobile
- [ ] "View Details" button: Easy to tap

#### TranscriptViewer (`/components/TranscriptViewer.tsx`)
**Test when transcript is present:**
- [ ] Header row: Can click to expand/collapse
- [ ] Timestamp column: Visible and readable
- [ ] Speaker column: Readable without truncation
- [ ] Text column: Readable line length on mobile
- [ ] NO horizontal scroll at 375px width
- [ ] Touch-friendly: Can expand/collapse with thumb

**Good transcript layout:**
```
[00:00] Therapist: Hello, how are you today?
[00:05] Client: I'm doing well, thanks for asking.
```

**Bad transcript layout (don't do):**
```
[00:00] Therapist:                    Hello, how are you today?
        (only 100px left for text)
```

#### SessionUploader (`/components/SessionUploader.tsx`)
**Test drag-and-drop zone:**
- [ ] Padding appropriate on mobile (not cramped)
- [ ] Icon size responsive
- [ ] Text size responsive
- [ ] "Select File" button: Full-width on mobile
- [ ] Error message: Readable and not cutoff
- [ ] Dragging state: Visual feedback is clear

#### Cards (Strategy, Trigger, ActionItem)
**Test each card type:**
- [ ] Title: Doesn't squeeze with badges
- [ ] Badge: Doesn't wrap awkwardly
- [ ] Content: Readable with good spacing
- [ ] Checkbox (ActionItem): 44px+ height on mobile

---

## Testing Methodology

### Using Chrome DevTools

1. Open DevTools (F12 or Right-click → Inspect)
2. Click device toggle (Ctrl+Shift+M)
3. Select viewport:
   - "iPhone SE" (375x667) - small phone
   - "iPhone 12/13" (390x844) - standard phone
   - "iPad Air" (820x1180) - tablet
   - Custom: 375, 640, 768, 1024 widths

### Testing Steps for Each Page

1. **Load page at target width**
   ```
   Set viewport width → Refresh page → Allow it to fully load
   ```

2. **Check visual layout**
   ```
   - No horizontal scroll?
   - All elements visible?
   - Text readable?
   - Spacing reasonable?
   ```

3. **Test interactions**
   ```
   - Buttons clickable?
   - Forms input-able?
   - Navigation works?
   - Dropdowns open correctly?
   ```

4. **Check touch targets**
   - Measure button/link heights (should be 44px+)
- Measure button/link widths (should be 44px+)

### Landscape Testing (Mobile)

For each mobile page, also test in landscape (e.g., 844x390 for iPhone 12):
- [ ] Still readable?
- [ ] Layout makes sense?
- [ ] No content cutoff?

---

## Common Issues and How to Spot Them

### 1. Text Overflow / Horizontal Scroll
**How to spot:**
- Page scrolls left/right
- Text is cut off
- Elements go beyond viewport edge

**Fix:** Add `px-4` or `px-6` padding, ensure max-widths are set correctly

### 2. Elements Squeezed Together
**How to spot:**
- Buttons are touching
- Text is truncated
- No breathing room

**Fix:** Add gap classes, stack with flex-col, use responsive spacing

### 3. Touch Targets Too Small
**How to spot:**
- Hard to click with finger
- Buttons less than 44px tall/wide

**Fix:** Increase min-height/min-width, add padding to clickable elements

### 4. Unresponsive Images/Content
**How to spot:**
- Images overflow container
- Fixed widths cause issues

**Fix:** Add responsive sizing (`w-full`, `max-w-full`), use responsive image sizes

### 5. Typography Too Large
**How to spot:**
- Text takes up full screen width
- Hard to read

**Fix:** Use responsive text sizes (`text-2xl sm:text-3xl`), ensure max line length ~65 chars

### 6. Layout Breaks at Specific Widths
**How to spot:**
- Page looks fine at 375px
- Breaks at 640px
- Seems to snap between states

**Fix:** Test at all breakpoints, adjust breakpoint values if needed

---

## Automated Testing

### Using Lighthouse (Chrome DevTools)

1. Open DevTools
2. Go to Lighthouse tab
3. Select "Mobile" or "Desktop"
4. Click "Analyze page load"
5. Check "Accessibility" score (includes mobile usability)

### Using Responsive Design Mode Extensions

- [Responsive Design Mode](https://chrome.google.com/webstore/) - Chrome extension
- [Responsive Design Mode](https://addons.mozilla.org/en-US/firefox/addon/responsive-design-mode-plus/) - Firefox extension

---

## Before-After Comparison

### Before (Current Issues)

**Auth Login page at 375px:**
```
┌─────────────────────────┐
│  [form - no padding]    │  ← No horizontal padding
│  Too close to edges     │
└─────────────────────────┘
```

**Session Detail at 375px:**
```
┌─────────────────────────┐
│ Long Title Badge        │  ← Squeeze together
│ [mood indicator]        │
└─────────────────────────┘
```

### After (Expected Results)

**Auth Login page at 375px:**
```
┌─────────────────────────┐
│  [PADDING]              │
│  ┌───────────────────┐  │
│  │     [form]        │  │  ← Good padding + breathing room
│  └───────────────────┘  │
│  [PADDING]              │
└─────────────────────────┘
```

**Session Detail at 375px:**
```
┌─────────────────────────┐
│ Long Title              │  ← Stacked layout
│ Status Badge            │
│ [mood indicator]        │
│                         │
│ ├─ Time info            │
│ └─ Duration info        │
└─────────────────────────┘
```

---

## Final Validation Checklist

Before marking responsive design as complete:

- [ ] All pages tested at 375px (smallest phone)
- [ ] All pages tested at 640px (landscape phone / small tablet)
- [ ] All pages tested at 768px (tablet)
- [ ] All pages tested at 1024px+ (desktop)
- [ ] No horizontal scroll at any breakpoint
- [ ] All touch targets are 44px or larger
- [ ] All text is readable (not too small or too large)
- [ ] Navigation is accessible on mobile
- [ ] Forms work on mobile
- [ ] All interactive elements are easily tappable
- [ ] Images don't overflow containers
- [ ] No "broken" layouts at edge cases
- [ ] Landscape orientation works for mobile pages
- [ ] Error messages are visible and readable
- [ ] Loading indicators are visible
- [ ] Success/failure states are clear

---

## Tools & Resources

### Chrome DevTools
- Device Emulation: `Ctrl+Shift+M`
- Responsive Design Mode: `Ctrl+Shift+C` then device menu
- Mobile Network Throttling: DevTools → Network → "Slow 4G"

### Browser Testing
- [BrowserStack](https://www.browserstack.com/) - Real device testing
- [Sauce Labs](https://saucelabs.com/) - Cross-browser testing
- [Chrome Device Lab](https://developers.google.com/web/tools/chrome-devtools/device-mode) - Built-in emulation

### Design Tools
- [Figma Mobile UI Kit](https://www.figma.com/) - Design reference
- [Material Design](https://material.io/) - Google's mobile design guidelines
- [Apple Human Interface](https://developer.apple.com/design/human-interface-guidelines) - Apple's guidelines

### Accessibility
- [WCAG Mobile Accessibility](https://www.w3.org/WAI/WCAG21/quickref/) - Accessibility standards
- [axe DevTools](https://www.deque.com/axe/devtools/) - Accessibility testing browser extension
