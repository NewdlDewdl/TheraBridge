# Responsive Design Patterns - Quick Reference

## Tailwind Breakpoints (TherapyBridge)

```
Mobile First Architecture:
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [Mobile]   [Landscape]   [Tablet]    [Desktop]   [Large]      │
│  0-640px    640px         768px       1024px       1280px       │
│  (base)     (sm:)         (md:)       (lg:)        (xl:)        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

DEFAULT = Mobile styles (no prefix)
sm: = 640px and up
md: = 768px and up
lg: = 1024px and up
xl: = 1280px and up
```

---

## Common Patterns

### Pattern 1: Responsive Grid

```tsx
// Single column on mobile, adapts on larger screens
<div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
  <Card>Item 1</Card>
  <Card>Item 2</Card>
  <Card>Item 3</Card>
</div>

Visual:
Mobile (375px):
┌─────────────────┐
│     Card 1      │
├─────────────────┤
│     Card 2      │
├─────────────────┤
│     Card 3      │
└─────────────────┘

Tablet (768px):
┌──────────────┬──────────────┐
│    Card 1    │    Card 2    │
├──────────────┼──────────────┤
│    Card 3    │              │
└──────────────┴──────────────┘

Desktop (1024px+):
┌──────────┬──────────┬──────────┐
│ Card 1   │ Card 2   │ Card 3   │
└──────────┴──────────┴──────────┘
```

---

### Pattern 2: Stack on Mobile, Row on Desktop

```tsx
// Stacks vertically on mobile, horizontal on larger screens
<div className="flex flex-col sm:flex-row gap-4">
  <Button>Button 1</Button>
  <Button>Button 2</Button>
</div>

Visual:
Mobile (375px):
┌──────────────────┐
│    Button 1      │
├──────────────────┤
│    Button 2      │
└──────────────────┘

Desktop (1024px+):
┌─────────────┬─────────────┐
│  Button 1   │  Button 2   │
└─────────────┴─────────────┘
```

---

### Pattern 3: Responsive Padding

```tsx
// Tighter on mobile, looser on desktop
<div className="px-4 sm:px-6 md:px-8 py-4 sm:py-6 md:py-8">
  <p>Content with responsive padding</p>
</div>

Visual:
Mobile (375px):        Desktop (1024px+):
│←4px→|        |←4px→│  │←8px→|                  |←8px→│
┌────────────────────┐  ┌──────────────────────────────┐
│  Content           │  │  Content                      │
└────────────────────┘  └──────────────────────────────┘
```

---

### Pattern 4: Responsive Typography

```tsx
// Smaller on mobile, larger on desktop
<h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">
  Responsive Title
</h1>

Visual:
Mobile:    Tablet:    Desktop:
Responsive Responsive Responsive
Title      Title      Title
(24px)     (30px)     (36px)
```

---

### Pattern 5: Hide/Show Elements

```tsx
// Hide on mobile, show on desktop
<div className="hidden sm:block">
  This only appears on sm and larger screens
</div>

// Show on mobile, hide on desktop
<div className="block sm:hidden">
  This only appears on mobile
</div>

// Alternative: Only show on specific breakpoints
<div className="hidden md:block lg:hidden">
  Only visible on tablet (md breakpoint)
</div>
```

---

### Pattern 6: Responsive Flex Direction

```tsx
// Vertical layout on mobile, horizontal on tablet+
<div className="flex flex-col md:flex-row gap-4">
  <div className="flex-1">Left Content</div>
  <div className="flex-1">Right Content</div>
</div>

Visual:
Mobile (375px):        Desktop (1024px+):
┌──────────────┐      ┌────────┬────────┐
│ Left Content │      │ Left   │ Right  │
├──────────────┤      │ Cont   │ Cont   │
│Right Content │      │        │        │
└──────────────┘      └────────┴────────┘
```

---

### Pattern 7: Responsive Gaps

```tsx
// Tighter spacing on mobile, looser on desktop
<div className="grid gap-2 sm:gap-4 md:gap-6">
  {/* items */}
</div>

Visual:
Mobile: 2px gap
Tablet: 4px gap
Desktop: 6px gap
```

---

### Pattern 8: Responsive Width & Max-Width

```tsx
// Full width on mobile, constrained on desktop
<div className="w-full max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg">
  <input type="text" />
</div>

Visual:
Mobile (375px):        Desktop (1024px+):
│←full width→│         │←full width→│
┌─────────────────┐    ┌──────┐
│ [Input]         │    │[In]  │
└─────────────────┘    └──────┘
```

---

### Pattern 9: Responsive Font Size

```tsx
// Multiple responsive text sizes
<p className="text-xs sm:text-sm md:text-base lg:text-lg">
  Responsive paragraph text
</p>

Sizes:
Mobile: 12px
Landscape: 14px
Tablet: 16px
Desktop: 18px
```

---

### Pattern 10: Responsive Container

```tsx
// Container with responsive padding
<div className="container mx-auto px-4 sm:px-6 md:px-8">
  <div className="max-w-6xl mx-auto">
    {/* content */}
  </div>
</div>

Visual:
Mobile:  │←4px→|content|←4px→│
Tablet:  │←6px→|content|←6px→│
Desktop: │←8px→|content|←8px→│
```

---

## Component-Specific Patterns

### Form Input (Mobile-Friendly)

```tsx
<div className="space-y-4">
  <div>
    <label className="block text-sm font-medium mb-2">
      Email
    </label>
    <input
      type="email"
      className="w-full px-4 py-3 sm:py-2 text-base sm:text-sm"
    />
  </div>
</div>

Key Points:
- py-3 on mobile (44px height for touch)
- py-2 on desktop (smaller, still usable)
- Full width on mobile
```

---

### Card Layout (Responsive)

```tsx
<div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
  <Card className="p-4 sm:p-6">
    <h3 className="text-base sm:text-lg font-semibold mb-2 sm:mb-4">
      Card Title
    </h3>
    <p className="text-sm sm:text-base text-muted-foreground">
      Card description
    </p>
  </Card>
</div>

Adapts: Padding, gaps, columns, typography
```

---

### Navigation (Responsive)

```tsx
<nav className="flex flex-col sm:flex-row gap-2 sm:gap-4">
  <Link className="px-3 py-2 sm:px-4 text-sm sm:text-base">
    Home
  </Link>
  <Link className="px-3 py-2 sm:px-4 text-sm sm:text-base">
    About
  </Link>
</nav>

Mobile: Vertical stack
Desktop: Horizontal row
```

---

## Responsive Utilities Quick Guide

### Spacing
```tsx
// Padding
p-4              // all sides: 1rem
px-4 sm:px-6     // horizontal: 1rem → 1.5rem
py-4 sm:py-6     // vertical: 1rem → 1.5rem
pt-4 sm:pt-6     // top: 1rem → 1.5rem

// Gaps
gap-2 sm:gap-4   // 0.5rem → 1rem
space-y-2 sm:space-y-4  // vertical: 0.5rem → 1rem
space-x-2 sm:space-x-4  // horizontal: 0.5rem → 1rem
```

### Layout
```tsx
// Flex
flex flex-col sm:flex-row    // Stack → Row
flex items-center sm:items-start

// Grid
grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
gap-4 sm:gap-6

// Alignment
justify-start sm:justify-between
items-center sm:items-start
```

### Typography
```tsx
// Sizes
text-sm sm:text-base md:text-lg
text-base sm:text-xl md:text-2xl

// Other
font-medium sm:font-semibold
leading-relaxed sm:leading-tight
tracking-tight sm:tracking-normal
```

### Width/Height
```tsx
// Width
w-full sm:w-auto
w-12 sm:w-16
max-w-xs sm:max-w-sm md:max-w-md

// Height
h-10 sm:h-12
min-h-screen sm:min-h-fit
```

### Display
```tsx
// Visibility
hidden sm:block       // hide on mobile, show on sm+
block sm:hidden       // show on mobile, hide on sm+
block md:hidden       // show on mobile/tablet, hide on md+

// Responsive
md:absolute
lg:relative
sm:flex md:grid
```

---

## Common Mistakes to Avoid

### ❌ Wrong: Fixed width on desktop value
```tsx
<div className="w-64">  // Always 16rem (fixed)
  Content
</div>
```

### ✅ Right: Mobile-first with responsive
```tsx
<div className="w-full md:w-64">  // Full on mobile, 16rem on desktop
  Content
</div>
```

---

### ❌ Wrong: No mobile padding
```tsx
<div className="px-8">  // 2rem even on mobile (too tight)
  Content
</div>
```

### ✅ Right: Responsive padding
```tsx
<div className="px-4 sm:px-6 md:px-8">  // Scales with screen
  Content
</div>
```

---

### ❌ Wrong: Row layout always
```tsx
<div className="flex gap-4">  // Mobile will squeeze!
  <div className="flex-1">Left</div>
  <div className="flex-1">Right</div>
</div>
```

### ✅ Right: Stack on mobile
```tsx
<div className="flex flex-col sm:flex-row gap-4">
  <div className="flex-1">Left</div>
  <div className="flex-1">Right</div>
</div>
```

---

### ❌ Wrong: Hardcoded values
```tsx
<h1 className="text-4xl font-bold">  // Always large
  Title
</h1>
```

### ✅ Right: Responsive typography
```tsx
<h1 className="text-2xl sm:text-3xl md:text-4xl font-bold">
  Title
</h1>
```

---

## Touch Target Checklist

All interactive elements must be at least 44px × 44px:

```tsx
// ❌ Too small for touch
<button className="px-2 py-1">Small</button>
// Results in ~24px height

// ✅ Good for touch (mobile)
<button className="px-4 py-3 sm:py-2">Touch-friendly</button>
// 48px height on mobile, 40px on desktop

// ✅ Also good (dedicated touch-friendly sizing)
<button className="h-12 sm:h-10 px-4">
  Touch Target
</button>
// 48px on mobile, 40px on desktop
```

---

## Testing Your Responsive Layout

### Chrome DevTools Method

1. Open DevTools: F12
2. Toggle Device: Ctrl+Shift+M
3. Test sizes:
   - 375px (mobile)
   - 640px (landscape)
   - 768px (tablet)
   - 1024px (desktop)

### Checklist
- [ ] No horizontal scroll at any width
- [ ] Text readable without zoom
- [ ] Buttons/links are 44px+ tall
- [ ] Images don't overflow
- [ ] Spacing feels right (not too tight)
- [ ] Layout adapts smoothly

---

## Quick Copy-Paste Templates

### Responsive Card Grid
```tsx
<div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
  {items.map((item) => (
    <Card key={item.id} className="p-4 sm:p-6">
      <h3 className="text-base sm:text-lg font-semibold mb-2">
        {item.title}
      </h3>
      <p className="text-sm text-muted-foreground">
        {item.description}
      </p>
    </Card>
  ))}
</div>
```

---

### Responsive Form
```tsx
<div className="space-y-4">
  <div>
    <label className="block text-sm font-medium mb-2">
      Field Label
    </label>
    <input
      type="text"
      className="w-full px-4 py-3 sm:py-2 border rounded text-base sm:text-sm"
    />
  </div>
  <button className="w-full sm:w-auto px-6 py-3 sm:py-2 bg-primary text-white rounded">
    Submit
  </button>
</div>
```

---

### Responsive Navigation
```tsx
<header className="border-b">
  <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <Logo />
        <span className="hidden sm:inline text-lg font-bold">
          App Name
        </span>
      </div>
      <nav className="hidden sm:flex gap-4">
        {/* Navigation items */}
      </nav>
    </div>
  </div>
</header>
```

---

## Reference: Tailwind Values

### Common Spacing Values
```
p-2   = 0.5rem (8px)
p-3   = 0.75rem (12px)
p-4   = 1rem (16px)
p-6   = 1.5rem (24px)
p-8   = 2rem (32px)
```

### Common Gap Values
```
gap-1  = 0.25rem (4px)
gap-2  = 0.5rem (8px)
gap-3  = 0.75rem (12px)
gap-4  = 1rem (16px)
gap-6  = 1.5rem (24px)
```

### Common Text Sizes
```
text-xs   = 12px
text-sm   = 14px
text-base = 16px
text-lg   = 18px
text-xl   = 20px
text-2xl  = 24px
text-3xl  = 30px
text-4xl  = 36px
```

---

## Rule of Thumb

**When in doubt, follow this order:**

1. Write mobile styles first (no prefix)
2. Add tablet adjustments (md:)
3. Add desktop refinements (lg:)
4. Test at 375px, 768px, 1024px

**Result:** Your app works everywhere! 🚀

---

**Last Updated:** 2025-12-17
**Tailwind Version:** 3.x+
**Next.js Version:** 14+
