# Progress Indicators - Quick Start Guide

## What Was Created

A complete progress indicator system with 5 new components for displaying upload and multi-step processing status.

## Component Files

```
frontend/
├── components/
│   ├── ui/
│   │   ├── progress-bar.tsx          ← Reusable progress bar
│   │   └── step-indicator.tsx        ← Multi-step indicator
│   ├── SessionProgressTracker.tsx    ← Session workflow tracker
│   ├── SessionUploaderWithProgress.tsx ← Complete upload component
│   └── examples/
│       └── progress-indicator-demo.tsx ← Interactive demo
├── PROGRESS_COMPONENTS.md            ← Full documentation
└── PROGRESS_COMPONENTS_SUMMARY.md    ← Implementation overview
```

## Quick Examples

### 1. Simple Progress Bar
```tsx
import { ProgressBar } from '@/components/ui/progress-bar';

<ProgressBar
  value={65}
  showLabel={true}
  variant="default"
  size="md"
/>
```

### 2. Step-by-Step Progress
```tsx
import { StepIndicator } from '@/components/ui/step-indicator';

const steps = [
  { id: '1', label: 'Upload', description: 'Select file' },
  { id: '2', label: 'Process', description: 'Processing...' },
  { id: '3', label: 'Complete', description: 'Done' },
];

<StepIndicator
  steps={steps}
  currentStepIndex={1}
  orientation="horizontal"
/>
```

### 3. Session Upload with Real-Time Progress
```tsx
import { SessionProgressTracker } from '@/components/SessionProgressTracker';

<SessionProgressTracker
  session={sessionData}
  showDescriptions={true}
  title="Processing Your Session"
/>
```

### 4. Full Upload Flow
```tsx
import { SessionUploaderWithProgress } from '@/components/SessionUploaderWithProgress';

<SessionUploaderWithProgress
  patientId="patient-123"
  onUploadComplete={(sessionId) => {
    router.push(`/therapist/sessions/${sessionId}`);
  }}
  pollInterval={2000}
/>
```

## Component Features at a Glance

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| ProgressBar | Show percentage completion | Animated, multiple sizes, color variants |
| StepIndicator | Show process steps | Horizontal/vertical, clickable, icons |
| SessionProgressTracker | Track session processing | Real-time status, compact mode, error handling |
| SessionUploaderWithProgress | Upload with progress | Drag-drop, validation, polling, error recovery |
| Demo | Testing & reference | Interactive examples, code snippets |

## Color Variants

All progress components support 4 variants:
- **default** - Primary blue color
- **success** - Green (100% complete)
- **warning** - Yellow (in progress)
- **destructive** - Red (error)

## Session Workflow Steps

The SessionProgressTracker automatically maps backend statuses to UI:

```
uploading (25%)
    ↓
transcribing (50%)
    ↓
transcribed (50%)
    ↓
extracting_notes (75%)
    ↓
processed (100%) ✓
    ↓
[error] (failed)
```

## Integration Points

### Replace Existing Uploader
```tsx
// Old way
import { SessionUploaderOptimistic } from '@/components/SessionUploaderOptimistic';

// New way - drop-in replacement
import { SessionUploaderWithProgress } from '@/components/SessionUploaderWithProgress';
```

### Add to Session List
```tsx
<SessionProgressTracker session={session} compact={true} />
```

### Monitor Processing
```tsx
<SessionProgressTracker
  session={sessionData}
  title="Real-time Status"
/>
```

## Props Reference

### ProgressBar
```typescript
{
  value: number,           // 0-100
  showLabel?: boolean,     // default: true
  labelPosition?: 'inside' | 'above' | 'below' | 'none'
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'destructive'
  animated?: boolean,      // default: true
  label?: string | React.ReactNode
}
```

### StepIndicator
```typescript
{
  steps: Array<{ id, label, description?, status? }>
  currentStepIndex: number
  orientation?: 'horizontal' | 'vertical'
  showDescriptions?: boolean
  clickable?: boolean
  onStepClick?: (index) => void
}
```

### SessionProgressTracker
```typescript
{
  session: Session | null
  compact?: boolean        // default: false
  showDescriptions?: boolean
  title?: string
  description?: string
}
```

### SessionUploaderWithProgress
```typescript
{
  patientId: string
  onUploadComplete?: (sessionId) => void
  pollInterval?: number    // default: 2000ms
}
```

## Key Features

### Accessibility
- Full ARIA support
- Keyboard navigation
- Screen reader friendly
- Color contrast compliant

### Responsive
- Mobile-friendly
- Adapts to screen size
- Touch-friendly drag-drop

### Dark Mode
- Automatic dark theme
- Contrast adjusted
- Consistent colors

### Type-Safe
- Full TypeScript
- Type definitions included
- Generic types where applicable

## Common Patterns

### Show Upload Progress
```tsx
<ProgressBar value={uploadPercentage} />
```

### Show Multi-Stage Processing
```tsx
<SessionProgressTracker session={session} showDescriptions={true} />
```

### Minimal Inline Progress
```tsx
<SessionProgressTracker session={session} compact={true} />
```

### Interactive Step Selection
```tsx
<StepIndicator
  steps={steps}
  currentStepIndex={index}
  clickable={true}
  onStepClick={(i) => setIndex(i)}
/>
```

## Testing

See interactive demo:
```
npm run dev
# Navigate to components/examples/progress-indicator-demo.tsx
```

## Performance Tips

1. **Polling**: Default 2000ms is good for most cases
2. **Rendering**: Compact mode for list views
3. **Animations**: Disable if performance is an issue
4. **Updates**: Only update when status actually changes

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 15+
- Edge 90+
- Mobile browsers (iOS 13+, Android 9+)

## Troubleshooting

### Progress bar not updating?
- Check `value` prop is changing
- Verify percentage calculation is correct

### Steps not advancing?
- Ensure `currentStepIndex` is being updated
- Check backend status values match mapping

### Polling not working?
- Verify API endpoint returns correct status
- Check network tab for fetch requests
- Increase poll interval if server overloaded

## Files to Review

1. **PROGRESS_COMPONENTS.md** - Full documentation
2. **PROGRESS_COMPONENTS_SUMMARY.md** - Implementation details
3. **components/examples/progress-indicator-demo.tsx** - Live examples

## Next Steps

1. Copy `SessionUploaderWithProgress` usage to your pages
2. Add `SessionProgressTracker` to session list views
3. Test with real backend API
4. Adjust polling interval based on your needs
5. Customize colors if needed

## Styling Notes

- Uses Tailwind CSS
- Respects theme colors (primary, muted, destructive, etc.)
- Dark mode automatic via `dark:` utilities
- All colors customizable in component code

---

**Quick tip:** Start with `SessionUploaderWithProgress` for immediate upload tracking, then add `SessionProgressTracker` to session lists for real-time status monitoring.
