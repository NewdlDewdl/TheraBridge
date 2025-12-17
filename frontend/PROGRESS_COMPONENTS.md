# Progress Indicator Components

Complete documentation for progress indicator components used throughout the application for displaying multi-step processes and upload/processing status.

## Components Overview

### 1. ProgressBar
A reusable progress bar component with customizable appearance and labeling.

**Location:** `/components/ui/progress-bar.tsx`

#### Features
- Percentage-based progress display (0-100)
- Multiple size variants: `sm`, `md`, `lg`
- Color variants: `default`, `success`, `warning`, `destructive`
- Label positioning: `inside`, `above`, `below`, `none`
- Optional animated stripe pattern
- Fully accessible with ARIA attributes

#### Basic Usage
```tsx
import { ProgressBar } from '@/components/ui/progress-bar';

// Simple progress bar
<ProgressBar value={65} />

// With custom label and positioning
<ProgressBar
  value={75}
  label="Uploading file..."
  labelPosition="above"
  size="lg"
/>

// Success variant with animation disabled
<ProgressBar
  value={100}
  variant="success"
  animated={false}
/>
```

#### Props
```typescript
interface ProgressBarProps {
  value: number;              // Current progress (0-100)
  max?: number;               // Maximum value (default: 100)
  showLabel?: boolean;        // Show percentage text (default: true)
  labelPosition?: 'inside' | 'above' | 'below' | 'none';
  size?: 'sm' | 'md' | 'lg';  // Bar height
  variant?: 'default' | 'success' | 'warning' | 'destructive';
  animated?: boolean;         // Animated stripe pattern (default: true)
  label?: string | React.ReactNode;  // Custom label
  ariaLabel?: string;         // Accessibility label
}
```

---

### 2. StepIndicator
Multi-step progress indicator for visual representation of sequential processes.

**Location:** `/components/ui/step-indicator.tsx`

#### Features
- Horizontal and vertical orientations
- Step status tracking: `pending`, `in-progress`, `completed`, `error`
- Optional step descriptions
- Interactive step clicking capability
- Visual connectors between steps
- Smart status icons (pending circle, spinning clock, checkmark, error)

#### Basic Usage
```tsx
import { StepIndicator, type Step } from '@/components/ui/step-indicator';

const steps: Step[] = [
  {
    id: 'upload',
    label: 'Upload',
    description: 'Select your file',
    status: 'completed',
  },
  {
    id: 'process',
    label: 'Processing',
    description: 'Analyzing content',
    status: 'in-progress',
  },
  {
    id: 'complete',
    label: 'Complete',
    description: 'Done',
    status: 'pending',
  },
];

// Horizontal (default)
<StepIndicator
  steps={steps}
  currentStepIndex={1}
  orientation="horizontal"
  showDescriptions={true}
/>

// Vertical
<StepIndicator
  steps={steps}
  currentStepIndex={1}
  orientation="vertical"
  clickable={true}
  onStepClick={(index) => console.log('Step clicked:', index)}
/>
```

#### Props
```typescript
interface Step {
  id: string;
  label: string;
  description?: string;
  status?: 'pending' | 'in-progress' | 'completed' | 'error';
}

interface StepIndicatorProps {
  steps: Step[];
  currentStepIndex: number;
  orientation?: 'horizontal' | 'vertical';
  showDescriptions?: boolean;
  clickable?: boolean;
  onStepClick?: (stepIndex: number) => void;
}
```

#### Step Statuses
- **pending**: Not yet active, shown with empty circle icon
- **in-progress**: Currently active, shown with animated clock icon
- **completed**: Finished successfully, shown with green checkmark
- **error**: Failed, shown with red alert icon

---

### 3. SessionProgressTracker
Integrated component for tracking session upload and processing workflow.

**Location:** `/components/SessionProgressTracker.tsx`

#### Features
- Automatic status tracking based on session state
- Progress bar with percentage
- Step-by-step progress visualization
- Error and success message display
- Compact and full-size modes
- Maps backend session statuses to UI steps:
  - `uploading` → Upload phase (25%)
  - `transcribing` → Transcription phase (50%)
  - `transcribed` → Preparing for analysis (50%)
  - `extracting_notes` → Analysis phase (75%)
  - `processed` → Complete (100%)
  - `failed` → Error state

#### Basic Usage
```tsx
import { SessionProgressTracker } from '@/components/SessionProgressTracker';

// Full mode with descriptions
<SessionProgressTracker
  session={sessionData}
  showDescriptions={true}
  title="Session Processing Progress"
/>

// Compact mode for inline display
<SessionProgressTracker
  session={sessionData}
  compact={true}
/>

// Without session data yet
<SessionProgressTracker
  session={null}
  title="Preparing to upload..."
/>
```

#### Props
```typescript
interface SessionProgressTrackerProps {
  session: SessionResponse | null;
  compact?: boolean;
  showDescriptions?: boolean;
  title?: string;
  description?: string;
}
```

#### Session Workflow
1. **Uploading** (25%): File being sent to server
2. **Transcribing** (50%): Audio being converted to text
3. **Extracting Notes** (75%): AI analyzing the transcript
4. **Complete** (100%): All processing finished

---

### 4. SessionUploaderWithProgress
Complete upload component with integrated progress tracking.

**Location:** `/components/SessionUploaderWithProgress.tsx`

#### Features
- Drag-and-drop file upload
- File validation (type and size)
- Upload progress indicator
- Automatic polling for processing status
- Seamless transition from upload to processing
- Comprehensive error handling
- Multi-step progress visualization

#### Basic Usage
```tsx
import { SessionUploaderWithProgress } from '@/components/SessionUploaderWithProgress';
import { useRouter } from 'next/navigation';

export function MyComponent() {
  const router = useRouter();

  return (
    <SessionUploaderWithProgress
      patientId="patient-123"
      onUploadComplete={(sessionId) => {
        router.push(`/therapist/sessions/${sessionId}`);
      }}
      pollInterval={2000}  // Check status every 2 seconds
    />
  );
}
```

#### Props
```typescript
interface SessionUploaderWithProgressProps {
  patientId: string;
  onUploadComplete?: (sessionId: string) => void;
  pollInterval?: number;  // Polling interval in milliseconds (default: 2000)
}
```

#### Workflow
1. User selects or drags file
2. File is validated
3. Upload begins with progress indicator
4. After upload completes (100%), polling for processing status begins
5. SessionProgressTracker displays real-time processing status
6. On completion, callback is triggered
7. User can upload another file

---

## Integration Examples

### Example 1: Patient Session Upload
```tsx
'use client';

import { SessionUploaderWithProgress } from '@/components/SessionUploaderWithProgress';
import { useRouter } from 'next/navigation';

export function PatientUploadPage() {
  const router = useRouter();
  const patientId = 'patient-123'; // Get from URL params

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Upload Session Recording</h1>

      <SessionUploaderWithProgress
        patientId={patientId}
        onUploadComplete={(sessionId) => {
          router.push(`/therapist/sessions/${sessionId}`);
        }}
      />
    </div>
  );
}
```

### Example 2: Custom Progress Tracking
```tsx
import { ProgressBar } from '@/components/ui/progress-bar';
import { StepIndicator, type Step } from '@/components/ui/step-indicator';

export function CustomProgressExample() {
  const [progress, setProgress] = useState(0);

  const steps: Step[] = [
    { id: 'validate', label: 'Validate', status: 'completed' },
    { id: 'upload', label: 'Upload', status: 'in-progress' },
    { id: 'process', label: 'Process', status: 'pending' },
  ];

  return (
    <div className="space-y-6">
      <ProgressBar value={progress} size="lg" />
      <StepIndicator
        steps={steps}
        currentStepIndex={1}
        orientation="vertical"
        showDescriptions={true}
      />
    </div>
  );
}
```

### Example 3: Inline Progress Display
```tsx
import { SessionProgressTracker } from '@/components/SessionProgressTracker';

export function SessionListItem({ session }: { session: SessionResponse }) {
  return (
    <div className="p-4 border rounded-lg">
      <h3 className="font-semibold mb-4">{session.audio_filename}</h3>

      {/* Compact progress tracker for list items */}
      <SessionProgressTracker
        session={session}
        compact={true}
      />
    </div>
  );
}
```

---

## Styling and Theming

All components use Tailwind CSS and respect the app's theme system (light/dark mode).

### Color Variants
- **default**: Primary color scheme
- **success**: Green for completed/successful states
- **warning**: Yellow for in-progress/caution states
- **destructive**: Red for error states

### Responsive Design
- Components are mobile-friendly
- Step labels adapt to screen size
- Progress bars scale appropriately on small screens

### Dark Mode Support
All components automatically adapt to dark mode through Tailwind's `dark:` utilities.

---

## Accessibility

All components include proper accessibility features:

### ProgressBar
- `role="progressbar"` attribute
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax` attributes
- Customizable `aria-label`
- Text alternatives for visual progress

### StepIndicator
- `aria-current="step"` for active step
- Semantic HTML structure
- Keyboard navigation support
- Clear status indicators

### SessionProgressTracker
- Inherits accessibility from sub-components
- Descriptive status messages
- Error/success messaging

---

## Performance Considerations

### Polling Strategy (SessionUploaderWithProgress)
- Default poll interval: 2000ms (2 seconds)
- Adjustable via `pollInterval` prop
- Stops automatically when processing completes
- Exponential backoff on network errors (2x delay)

### Optimization Tips
1. Use `compact` mode for list items
2. Limit `showDescriptions` to detailed views
3. Adjust `pollInterval` based on expected processing time
4. Cache session data when possible

---

## API Integration

The components expect session data matching the `SessionResponse` type:

```typescript
interface SessionResponse {
  id: SessionId;
  status: 'uploading' | 'transcribing' | 'transcribed' |
          'extracting_notes' | 'processed' | 'failed';
  error_message: string | null;
  // ... other fields
}
```

The backend must return this structure for the progress tracker to work correctly.

---

## Demo Component

See `SessionUploaderWithProgress`, which demonstrates all components:

```bash
# View the demo page
npm run dev
# Navigate to /components/examples/progress-indicator-demo
```

---

## Troubleshooting

### Progress Not Updating
- Check that `pollInterval` is reasonable (too low = server overload)
- Verify backend is returning correct status values
- Check browser console for network errors

### Steps Not Progressing
- Ensure `currentStepIndex` is being updated
- Verify session status is changing on the backend
- Check that status values match `STATUS_TO_STEP_INDEX` mapping

### Progress Bar Not Showing
- Check that `value` prop is between 0-100
- Verify `showLabel` and `labelPosition` props
- Ensure parent container has sufficient width

---

## Best Practices

1. **Always provide feedback**: Use progress indicators for any process taking >1 second
2. **Clear messaging**: Explain what's happening at each step
3. **Error handling**: Always display error messages and provide recovery options
4. **Mobile-first**: Test components on mobile devices
5. **Accessibility**: Always include descriptive labels
6. **Performance**: Use polling sparingly; consider WebSockets for real-time updates

---

## Related Components

- `/components/SessionUploader.tsx` - Basic uploader without progress
- `/components/SessionUploaderOptimistic.tsx` - Optimistic UI updates
- `/components/ui/card.tsx` - Container components
- `/components/ui/button.tsx` - Action buttons
