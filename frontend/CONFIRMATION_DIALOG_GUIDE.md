# Confirmation Dialog Component Guide

## Overview

The Confirmation Dialog component provides a robust, accessible way to confirm destructive or important actions before they're executed. It uses native HTML `<dialog>` elements with a backdrop blur effect for a professional appearance.

## Key Features

- **Native HTML Dialog**: Uses HTML5 `<dialog>` element with proper modal behavior
- **Multiple Variants**: Default, warning, and destructive styles
- **Loading States**: Built-in support for async operations with loading indicators
- **Error Handling**: Display errors during confirmation without closing the dialog
- **Keyboard Support**: ESC to close, Enter to confirm
- **Accessibility**: Proper ARIA attributes and semantic HTML
- **Type-Safe**: Full TypeScript support with exported interfaces

## Installation

No additional dependencies needed! The component uses:
- React 19
- Lucide React (for icons)
- Tailwind CSS (for styling)
- Existing Radix UI components (only Button)

## Basic Usage

### Simple Confirmation

```tsx
import { useState } from 'react';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { Button } from '@/components/ui/button';

export function MyComponent() {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConfirm = async () => {
    // Your action here
    console.log('Action confirmed!');
  };

  return (
    <>
      <Button onClick={() => setShowConfirm(true)}>
        Perform Action
      </Button>

      <ConfirmationDialog
        isOpen={showConfirm}
        onOpenChange={setShowConfirm}
        title="Confirm Action"
        description="Are you sure you want to proceed?"
        onConfirm={handleConfirm}
        confirmLabel="Confirm"
        cancelLabel="Cancel"
      />
    </>
  );
}
```

## Component Props

```typescript
interface ConfirmationDialogProps {
  // Dialog state
  isOpen: boolean;                    // Controls dialog visibility
  onOpenChange: (open: boolean) => void;

  // Content
  title: string;                      // Main dialog title (required)
  description?: string;               // Secondary description text
  warning?: string;                   // Warning message in alert box

  // Actions
  onConfirm: () => void | Promise<void>;  // Handler for confirmation
  onCancel?: () => void;              // Optional cancel handler

  // Labels
  confirmLabel?: string;              // Confirm button text (default: "Confirm")
  cancelLabel?: string;               // Cancel button text (default: "Cancel")

  // Styling & behavior
  variant?: 'destructive' | 'default' | 'warning';  // Dialog variant
  isDangerous?: boolean;              // Makes confirm button destructive (default: false)
  isLoading?: boolean;                // Show loading state (handled by component)
  disabled?: boolean;                 // Disable all buttons

  // Ref forwarding (optional)
  // ref?: React.Ref<HTMLDialogElement>
}
```

## Variants & Styling

### 1. **Default Variant**

Standard confirmation for non-destructive actions.

```tsx
<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Confirm"
  description="Are you sure?"
  onConfirm={handleConfirm}
  variant="default"
/>
```

**Appearance**: Blue icon, standard styling

### 2. **Destructive Variant**

For delete operations and destructive changes.

```tsx
<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete Session?"
  description="Are you sure you want to delete this session?"
  onConfirm={handleDelete}
  variant="destructive"
  isDangerous={true}
  confirmLabel="Delete"
  cancelLabel="Keep"
/>
```

**Appearance**: Red icon, red confirm button, destructive styling

### 3. **Warning Variant**

For important actions that need attention but aren't destructive.

```tsx
<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Important Action"
  description="This will affect your settings"
  onConfirm={handleAction}
  variant="warning"
/>
```

**Appearance**: Amber icon, warning colors

## Advanced Usage

### With Warning Text

```tsx
<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete Session?"
  description="Delete the session for John Doe on Dec 17, 2025?"
  warning="This action is permanent and cannot be undone. All session data, transcript, and extracted notes will be deleted."
  onConfirm={handleDelete}
  variant="destructive"
  isDangerous={true}
/>
```

### With Async Operation

The component automatically shows a loading spinner during async operations:

```tsx
const handleAsyncConfirm = async () => {
  // API call
  const response = await fetch('/api/sessions/123', {
    method: 'DELETE'
  });

  if (!response.ok) {
    throw new Error('Failed to delete session');
  }
};

<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete?"
  onConfirm={handleAsyncConfirm}
  confirmLabel="Delete"
/>
```

### Error Handling

Errors during confirmation are displayed without closing the dialog:

```tsx
const handleWithError = async () => {
  try {
    await someFailableOperation();
  } catch (error) {
    throw error; // Shows error in dialog
  }
};

<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Perform Action?"
  onConfirm={handleWithError}
/>
```

## Real-World Examples

### Session Deletion

```tsx
import { SessionActionBar } from '@/components/session/SessionActionBar';

// In your session detail page
<SessionActionBar
  sessionId="session_123"
  patientName="Jane Doe"
  sessionDate="Dec 17, 2025"
/>
```

### Logout Confirmation

```tsx
import { LogoutButton } from '@/components/auth/LogoutButton';

// In your header/navigation
<LogoutButton />
```

### Custom Destructive Action

```tsx
export function DeletePatientButton({ patientId, patientName }) {
  const [showConfirm, setShowConfirm] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    const response = await fetch(`/api/patients/${patientId}`, {
      method: 'DELETE'
    });

    if (!response.ok) throw new Error('Failed to delete patient');

    router.push('/therapist');
  };

  return (
    <>
      <Button
        variant="destructive"
        onClick={() => setShowConfirm(true)}
      >
        Delete Patient
      </Button>

      <ConfirmationDialog
        isOpen={showConfirm}
        onOpenChange={setShowConfirm}
        title={`Delete ${patientName}?`}
        description="This patient and all associated sessions will be deleted."
        warning="This action cannot be undone."
        onConfirm={handleDelete}
        confirmLabel="Delete Patient"
        variant="destructive"
        isDangerous={true}
      />
    </>
  );
}
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `ESC` | Close dialog without confirming |
| `Enter` | Confirm action (when button has focus) |
| `Tab` | Navigate between buttons |

## Styling & Customization

The component uses Tailwind CSS with CSS variables for theming:

```css
/* Colors used (from tailwind.config.ts) */
--destructive: hsl(0, 84%, 60%)
--destructive-foreground: hsl(0, 0%, 100%)
--primary: hsl(217, 91%, 60%)
--muted-foreground: hsl(215, 13%, 34%)
```

### Custom Styling

To modify colors, edit `app/globals.css`:

```css
:root {
  --destructive: hsl(0, 84%, 60%);      /* Red for destructive actions */
  --warning: hsl(38, 92%, 50%);         /* Amber for warnings */
}
```

## Accessibility

The component includes:

- ✅ Semantic HTML (`<dialog>`, `<button>`, proper heading hierarchy)
- ✅ Keyboard navigation (ESC to close, Tab to navigate)
- ✅ Focus management (auto-focuses confirm button)
- ✅ ARIA attributes (proper roles and descriptions)
- ✅ Contrast ratios meeting WCAG AA standards
- ✅ Clear visual indicators for destructive actions

## Testing

### Unit Test Example

```tsx
import { render, screen } from '@testing-library/react';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

test('calls onConfirm when confirmed', async () => {
  const onConfirm = jest.fn();
  const { rerender } = render(
    <ConfirmationDialog
      isOpen={true}
      onOpenChange={() => {}}
      title="Test"
      onConfirm={onConfirm}
    />
  );

  const confirmButton = screen.getByText('Confirm');
  await userEvent.click(confirmButton);

  expect(onConfirm).toHaveBeenCalled();
});
```

## Related Hooks

### `useConfirmation()`

For managing dialog state automatically:

```tsx
const { confirm, isOpen, title, description, ... } = useConfirmation();

// Trigger confirmation
await confirm(
  {
    title: 'Delete?',
    description: 'Are you sure?',
    variant: 'destructive'
  },
  async () => { /* your action */ }
);
```

### `useDeleteSession()`

Specialized hook for session deletion:

```tsx
const { deleteSession, isLoading, error } = useDeleteSession();

await deleteSession({
  sessionId: '123',
  patientName: 'Jane Doe',
  onSuccess: () => router.push('/therapist')
});
```

### `useLogout()`

Specialized hook for logout operations:

```tsx
const { performLogout, isLoading } = useLogout();

await performLogout(); // Logs out and redirects to login
```

## Files Created

- `/components/ui/confirmation-dialog.tsx` - Main component
- `/components/session/SessionActionBar.tsx` - Session delete example
- `/components/auth/LogoutButton.tsx` - Logout example
- `/hooks/use-confirmation.ts` - Generic confirmation hook
- `/hooks/use-delete-session.ts` - Session deletion hook
- `/hooks/use-logout.ts` - Logout hook
- `/components/ConfirmationDialogDemo.tsx` - Interactive demo

## Troubleshooting

### Dialog Not Showing

Ensure `isOpen` is true and `onOpenChange` updates state correctly:

```tsx
const [isOpen, setIsOpen] = useState(false);

<ConfirmationDialog
  isOpen={isOpen}                    // Must be true
  onOpenChange={setIsOpen}          // Must update state
  // ... other props
/>
```

### Async Loading Not Working

Return a Promise from `onConfirm`:

```tsx
// ✅ Correct
onConfirm={async () => {
  await fetch(...);
}}

// ❌ Incorrect
onConfirm={() => {
  fetch(...); // Not awaited
}}
```

### Dialog Closing Too Early

Don't manually close the dialog when `onConfirm` is async:

```tsx
// ❌ Wrong - closes before API call completes
onConfirm={async () => {
  setShowConfirm(false);
  await deleteSession();
}}

// ✅ Correct - let component handle closing
onConfirm={async () => {
  await deleteSession();
}}
```

## Best Practices

1. **Always use destructive variant for deletions**
   - Helps users understand the severity
   - Uses red color as visual warning

2. **Include warning text for critical actions**
   - Explain what will happen
   - Mention if action is irreversible

3. **Use clear, action-oriented labels**
   - "Delete Session" instead of "Yes"
   - "Keep Session" instead of "No"

4. **Handle errors gracefully**
   - Display errors in the dialog
   - Don't close dialog on error
   - Allow user to retry

5. **Disable buttons during loading**
   - Prevents double-clicks
   - Shows operation is in progress
   - Handled automatically by component

6. **Test keyboard navigation**
   - ESC should close without confirming
   - Tab should navigate buttons
   - Enter should confirm on focused button

## Future Enhancements

Potential features to add:

- [ ] Custom icon support
- [ ] Multiple action buttons (Save, Delete, Archive)
- [ ] Checkbox confirmation (e.g., "I understand this is permanent")
- [ ] Animation customization
- [ ] Portal rendering for better z-index handling
- [ ] Integration with toast notifications

## Performance Notes

- Dialog is lightweight using native HTML elements
- No external animation libraries
- CSS transitions only (hardware-accelerated)
- Minimal re-renders with proper state management
- Auto-cleanup of event listeners

## Browser Support

Works on all modern browsers:
- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Full support

Fallback for older browsers using `::backdrop` polyfill (included in Tailwind).
