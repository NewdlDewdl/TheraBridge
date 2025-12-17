# Mobile Responsiveness Review

## Executive Summary

The frontend has **mixed mobile responsiveness**. While many pages use Tailwind's responsive prefixes (md:, lg:), there are critical gaps in mobile optimization, particularly around **fixed widths, narrow screens, and layout stacking**.

## Issues Found

### CRITICAL (Mobile unusable)

1. **Auth Pages (Login/Signup) - FIXED WIDTH ON MOBILE**
   - Location: `/app/auth/login/page.tsx` and `/app/auth/signup/page.tsx`
   - Issue: Forms use `max-w-md w-full` in center div, but don't specify responsive padding
   - Problem: On mobile, padding might squeeze the form too much
   - Fix: Add `px-4 sm:px-6` to form container

2. **Therapist Header Navigation - NON-RESPONSIVE**
   - Location: `/app/therapist/layout.tsx`
   - Issue: Header has hardcoded `gap-8` between logo and nav, no mobile collapse
   - Problem: On small screens, logo + "Therapist Dashboard" text takes up space, nav items get cramped
   - Fix: Hide nav label on mobile, stack vertically on sm:

3. **Patient Header Navigation - NON-RESPONSIVE**
   - Location: `/app/patient/layout.tsx`
   - Issue: Same as therapist layout
   - Fix: Ensure header is touch-friendly on mobile

### HIGH (Difficult to use on mobile)

4. **Home Page Hero Section - NARROW VIEWPORT ISSUES**
   - Location: `/app/page.tsx` line 24-37
   - Issue: Buttons in hero (`<div className="flex gap-4 justify-center pt-4">`)
   - Problem: On mobile (< 380px), two full-width buttons side-by-side won't fit
   - Fix: Add `flex-col sm:flex-row` to make buttons stack on mobile

5. **Patient Detail Page - STATS CARDS DON'T STACK**
   - Location: `/app/therapist/patients/[id]/page.tsx` line 86
   - Issue: `grid gap-4 md:grid-cols-3` means on mobile it's 1 column which is good
   - BUT: The flex layout inside cards (line 89) doesn't handle small screens well
   - Fix: Change inner flex to `flex-col sm:flex-row` for small card layouts

6. **Session Detail Page - TITLE & MOOD LAYOUT BREAKS**
   - Location: `/app/therapist/sessions/[id]/page.tsx` line 80-86
   - Issue: `<div className="flex items-start justify-between">` doesn't wrap on mobile
   - Problem: Title + Badge + Mood Indicator squeeze together
   - Fix: Add `md:flex-row flex-col gap-4` with responsive adjustments

7. **Transcript Viewer - OVERFLOW ON MOBILE**
   - Location: `/components/TranscriptViewer.tsx` line 43-51
   - Issue: Speaker name is fixed width (`w-20`), text doesn't wrap well
   - Problem: On mobile, layout breaks into 3 columns: timestamp, speaker, text
   - Fix: Change to `flex-col sm:flex-row` and responsive widths

### MEDIUM (Suboptimal but functional)

8. **Therapist Dashboard - PATIENT CARDS GRID**
   - Location: `/app/therapist/page.tsx` line 89
   - Issue: `grid gap-6 md:grid-cols-2 lg:grid-cols-3` - defaults to 1 column on mobile
   - This is good, BUT card content is tight
   - Fix: Review padding on small screens

9. **Patient Portal - STATS CARDS**
   - Location: `/app/patient/page.tsx` line 49
   - Issue: `grid gap-4 md:grid-cols-2` is good
   - BUT: Icon + text layout uses fixed spacing
   - Fix: Ensure `gap-4` is responsive (consider `sm:gap-2 md:gap-4`)

10. **Session Cards - LAYOUT ISSUES**
    - Location: `/components/SessionCard.tsx` line 22-35
    - Issue: `flex items-start justify-between` doesn't stack on mobile
    - Problem: Session date + badge squeeze together
    - Fix: Add responsive flex direction

11. **Buttons & Form Inputs - TOUCH TARGETS**
    - Multiple locations
    - Issue: Some buttons/inputs might be too small for touch (< 44px height)
    - Fix: Ensure minimum 44px height for touch targets

12. **Session Uploader - NO RESPONSIVE PADDING**
    - Location: `/components/SessionUploader.tsx` line 115
    - Issue: `p-8` is fixed, no mobile reduction
    - Fix: Change to `p-6 sm:p-8`

### LOW (Cosmetic)

13. **Typography Sizes - LARGE ON MOBILE**
    - Location: Multiple pages
    - Issue: `text-3xl font-bold` on mobile might be too large
    - Fix: Consider `text-2xl sm:text-3xl` for better mobile scaling

## File-by-File Recommendations

### Pages

#### `/app/page.tsx` - Home
**Issues:**
- Line 18: `text-5xl` hero title too large on mobile
- Line 24-37: Button row needs `flex-col sm:flex-row`

**Fixes:**
```tsx
// Line 18
<h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight">TherapyBridge</h1>

// Line 24-37
<div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
```

#### `/app/therapist/page.tsx` - Therapist Dashboard
**Issues:**
- Line 59-69: Header layout doesn't stack on mobile

**Fixes:**
```tsx
// Line 59-69
<div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0">
  <div>
    <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Patients</h2>
    <p className="text-muted-foreground text-sm sm:text-base">
      Manage your patients and their therapy sessions
    </p>
  </div>
  <Button className="w-full sm:w-auto">
    <Plus className="w-4 h-4 mr-2" />
    Add Patient
  </Button>
</div>
```

#### `/app/patient/page.tsx` - Patient Portal
**Issues:**
- Line 49: Stats grid responsive but could improve spacing
- Line 42: Outer container has `max-w-4xl` which is good, but needs padding

**Fixes:**
```tsx
// Line 42
<div className="space-y-6 sm:space-y-8 max-w-4xl mx-auto px-4 sm:px-6 lg:px-0">

// Line 49
<div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2">
```

#### `/app/auth/login/page.tsx` - Login Page
**Issues:**
- Line 50: `max-w-md w-full bg-white p-8` needs responsive padding
- No horizontal padding specified

**Fixes:**
```tsx
// Line 49-50
<div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
  <div className="max-w-md w-full bg-white p-6 sm:p-8 rounded-lg shadow-md">
```

#### `/app/auth/signup/page.tsx` - Signup Page
**Issues:**
- Same as login page
- Line 57-58: Same fix needed

**Fixes:**
```tsx
// Line 57-58
<div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 sm:px-6 lg:px-8">
  <div className="max-w-md w-full bg-white p-6 sm:p-8 rounded-lg shadow-md">
```

#### `/app/therapist/patients/[id]/page.tsx` - Patient Detail
**Issues:**
- Line 68: Title layout doesn't stack
- Line 86: Stats grid uses `md:grid-cols-3` but card content needs adjustment
- Line 155: Session grid uses `md:grid-cols-2 lg:grid-cols-3` which is good

**Fixes:**
```tsx
// Line 68-84
<div className="flex flex-col gap-4 sm:gap-6">
  <div className="flex items-start justify-between">
    <div>
      <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{patient.name}</h2>
      <div className="flex flex-col gap-2 mt-3 sm:mt-2">
        {/* contact info */}
      </div>
    </div>
  </div>

  <div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
    {/* stat cards */}
  </div>
</div>

// Line 155
<div className="grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
```

#### `/app/therapist/sessions/[id]/page.tsx` - Session Detail
**Issues:**
- Line 80-104: Header has flex with justify-between that breaks on mobile
- Line 155-163: Key topics badge row needs responsive handling

**Fixes:**
```tsx
// Line 80-104
<div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
  <div className="space-y-2 flex-1">
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <CardTitle className="text-xl sm:text-2xl">
        {patient ? `${patient.name}'s Session` : 'Session Details'}
      </CardTitle>
      <SessionStatusBadge status={session.status} />
    </div>
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm text-muted-foreground">
      {/* date/time info */}
    </div>
  </div>
  {notes?.session_mood && (
    <div className="mt-4 md:mt-0">
      <MoodIndicator mood={notes.session_mood} trajectory={notes.mood_trajectory} />
    </div>
  )}
</div>

// Line 168
<div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2">

// Line 206
<div className="grid gap-3 sm:gap-3 grid-cols-1 md:grid-cols-2">
```

### Layouts

#### `/app/therapist/layout.tsx`
**Issues:**
- Line 12-35: Header doesn't collapse on mobile
- Line 14: `gap-8` is too large on mobile

**Fixes:**
```tsx
<header className="border-b">
  <div className="container mx-auto px-4 py-3 sm:py-4">
    <div className="flex items-center justify-between gap-4 sm:gap-8">
      <Link href="/therapist" className="flex items-center gap-2 flex-shrink-0">
        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
          <Users className="w-6 h-6 text-primary-foreground" />
        </div>
        <div className="hidden sm:block">
          <h1 className="text-lg sm:text-xl font-bold">TherapyBridge</h1>
          <p className="text-xs text-muted-foreground">Therapist Dashboard</p>
        </div>
      </Link>
      <nav className="hidden sm:flex items-center gap-2 sm:gap-4">
        <Link
          href="/therapist"
          className="flex items-center gap-2 px-2 sm:px-3 py-2 text-xs sm:text-sm hover:bg-accent rounded-md transition-colors"
        >
          <Home className="w-4 h-4" />
          <span className="hidden sm:inline">Patients</span>
        </Link>
      </nav>
    </div>
  </div>
</header>
<main className="container mx-auto px-4 py-6 sm:py-8">
  {children}
</main>
```

#### `/app/patient/layout.tsx`
**Issues:**
- Same as therapist layout
- Line 13-21: Header doesn't adapt to mobile

**Fixes:**
```tsx
<header className="border-b">
  <div className="container mx-auto px-4 py-3 sm:py-4">
    <Link href="/patient" className="flex items-center gap-2">
      <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
        <Heart className="w-6 h-6 text-white" />
      </div>
      <div className="hidden sm:block">
        <h1 className="text-lg sm:text-xl font-bold">TherapyBridge</h1>
        <p className="text-xs text-muted-foreground">Your Progress</p>
      </div>
    </Link>
  </div>
</header>
<main className="container mx-auto px-4 py-6 sm:py-8">
  {children}
</main>
```

### Components

#### `/components/SessionCard.tsx`
**Issues:**
- Line 22-35: `flex items-start justify-between` doesn't wrap

**Fixes:**
```tsx
<Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
  <CardHeader className="pb-3">
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
      <div className="space-y-1 flex-1">
        {/* content */}
      </div>
      <div className="flex-shrink-0">
        <SessionStatusBadge status={session.status} />
      </div>
    </div>
  </CardHeader>
  {/* rest of card */}
</Card>
```

#### `/components/TranscriptViewer.tsx`
**Issues:**
- Line 43-51: 3-column layout (timestamp, speaker, text) breaks on mobile
- Line 48: `w-20` speaker width is too fixed

**Fixes:**
```tsx
<div className="space-y-2 sm:space-y-4 max-h-[600px] overflow-y-auto">
  {segments ? (
    segments.map((segment, index) => (
      <div
        key={index}
        className="flex flex-col sm:flex-row gap-2 sm:gap-4 p-2 sm:p-3 hover:bg-accent rounded-md transition-colors text-sm"
      >
        <div className="flex-shrink-0 text-xs text-muted-foreground font-mono sm:w-16">
          [{formatTimestamp(segment.start)}]
        </div>
        <div className="flex-shrink-0 font-semibold text-xs sm:text-sm sm:w-20">
          {segment.speaker}:
        </div>
        <div className="flex-1 text-xs sm:text-sm">{segment.text}</div>
      </div>
    ))
  ) : (
    <div className="whitespace-pre-wrap text-sm">{transcriptText}</div>
  )}
</div>
```

#### `/components/SessionUploader.tsx`
**Issues:**
- Line 115: `p-8` is too large on mobile
- Line 130-168: Icon and text don't scale down

**Fixes:**
```tsx
<div
  onDragOver={handleDragOver}
  onDragLeave={handleDragLeave}
  onDrop={handleDrop}
  onClick={() => !isUploading && fileInputRef.current?.click()}
  className={`
    relative border-2 border-dashed rounded-lg p-4 sm:p-6 md:p-8 text-center
    transition-all cursor-pointer
    ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50'}
    ${isUploading ? 'opacity-60 pointer-events-none' : ''}
  `}
>
  <div className="flex flex-col items-center gap-3 sm:gap-4">
    {isUploading ? (
      <>
        <Loader2 className="w-8 sm:w-12 h-8 sm:h-12 text-primary animate-spin" />
        <div className="space-y-1 sm:space-y-2">
          <p className="text-base sm:text-lg font-medium">Uploading session...</p>
          {selectedFile && (
            <p className="text-xs sm:text-sm text-muted-foreground break-all">{selectedFile.name}</p>
          )}
        </div>
      </>
    ) : (
      <>
        <div className="w-12 sm:w-16 h-12 sm:h-16 rounded-full bg-primary/10 flex items-center justify-center">
          {selectedFile ? (
            <File className="w-6 sm:w-8 h-6 sm:h-8 text-primary" />
          ) : (
            <Upload className="w-6 sm:w-8 h-6 sm:h-8 text-primary" />
          )}
        </div>
        <div className="space-y-1 sm:space-y-2 max-w-xs">
          <p className="text-base sm:text-lg font-medium break-all">
            {selectedFile ? selectedFile.name : 'Upload Audio File'}
          </p>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Drag and drop or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supported: {ALLOWED_EXTENSIONS.join(', ')}
          </p>
        </div>
        {!selectedFile && (
          <Button variant="secondary" type="button" className="w-full sm:w-auto">
            Select File
          </Button>
        )}
      </>
    )}
  </div>
  {/* error handling */}
</div>
```

#### `/components/StrategyCard.tsx`
**Issues:**
- Line 28-33: `flex items-start justify-between` might squeeze on narrow screens

**Fixes:**
```tsx
<Card>
  <CardHeader className="pb-3">
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
      <CardTitle className="text-sm sm:text-base">{strategy.name}</CardTitle>
      <Badge variant="outline" className={`${categoryColors[strategy.category]} flex-shrink-0`}>
        {strategy.category}
      </Badge>
    </div>
  </CardHeader>
  {/* rest of card */}
</Card>
```

#### `/components/TriggerCard.tsx`
**Issues:**
- Same as StrategyCard

**Fixes:**
```tsx
<Card>
  <CardHeader className="pb-3">
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
      <div className="flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
        <CardTitle className="text-sm sm:text-base">{trigger.trigger}</CardTitle>
      </div>
      <Badge variant="outline" className={`${className} flex-shrink-0`}>
        {label}
      </Badge>
    </div>
  </CardHeader>
  {/* rest of card */}
</Card>
```

#### `/components/ActionItemCard.tsx`
**Issues:**
- Line 20-35: Layout is good but could improve spacing on mobile

**Fixes:**
```tsx
<Card className={completed ? 'opacity-60' : ''}>
  <CardContent className="pt-4 sm:pt-6">
    <div className="flex items-start gap-2 sm:gap-3">
      <Checkbox
        checked={completed}
        onCheckedChange={(checked) => setCompleted(!!checked)}
        className="mt-0.5 sm:mt-1 flex-shrink-0"
      />
      <div className="flex-1 space-y-1 sm:space-y-2">
        <p className={`text-xs sm:text-sm font-medium ${completed ? 'line-through' : ''}`}>
          {actionItem.task}
        </p>
        <Badge variant="secondary" className="text-xs">
          {actionItem.category}
        </Badge>
        <p className="text-xs sm:text-sm text-muted-foreground">{actionItem.details}</p>
      </div>
    </div>
  </CardContent>
</Card>
```

## Tailwind Responsive Pattern Guide

Use these patterns consistently across all pages:

### Stacking Layouts
```tsx
// Single to multi-column
<div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

// Flex row to column
<div className="flex flex-col md:flex-row gap-4">

// Hide on mobile
<div className="hidden sm:block">

// Show only on mobile
<div className="block sm:hidden">
```

### Responsive Sizing
```tsx
// Text sizes
<h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">

// Padding
<div className="p-4 sm:p-6 md:p-8">

// Gaps
<div className="gap-2 sm:gap-4 md:gap-6">

// Width constraints
<div className="max-w-sm sm:max-w-md md:max-w-lg">
```

### Touch Targets (Mobile)
All buttons and interactive elements should be at least 44px tall and 44px wide.

## Testing Checklist

### Mobile (375px - 425px - typical phone)
- [ ] Home page hero title is readable
- [ ] Hero buttons stack vertically
- [ ] Navigation is accessible (not too small)
- [ ] Forms don't overflow
- [ ] Session cards are readable
- [ ] Transcript viewer doesn't have horizontal scroll
- [ ] Patient/Therapist list is scannable
- [ ] Touch targets are at least 44px

### Tablet (768px - 1024px - typical tablet)
- [ ] 2-column grids display properly
- [ ] Header navigation is visible
- [ ] Tables/lists are readable
- [ ] Forms are well-spaced
- [ ] Transcript has good line lengths (not too wide)

### Desktop (1024px+ - typical laptop)
- [ ] 3-column grids display properly
- [ ] Multi-section layouts work
- [ ] Text line lengths are reasonable (< 80 characters)
- [ ] Spacing provides good visual hierarchy

## Priority Implementation Order

1. **Critical (Do First):**
   - Auth pages: Add responsive padding
   - Hero buttons: Stack on mobile
   - Session detail header: Fix flex layout

2. **High (Do Next):**
   - Therapist/Patient layout headers
   - Transcript viewer responsive layout
   - Title + stats layout responsiveness

3. **Medium (Polish):**
   - Component card layouts
   - Spacing adjustments
   - Typography scaling

4. **Low (Nice to Have):**
   - Fine-tune breakpoints
   - Cosmetic adjustments
   - Animation responsiveness

## Notes for Implementation

- Always test at actual viewport sizes, not browser zoom
- Use Chrome DevTools device emulation for testing
- Consider landscape orientation on mobile
- Ensure 44px+ touch targets
- Test with actual touch interactions (not just mouse)
- Verify form inputs are accessible on mobile
- Check that error messages are visible and readable
