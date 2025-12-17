# Confirmation Dialog Integration Guide

## Quick Start

The confirmation dialog component has been created and is ready to use. This guide shows you how to integrate it into your existing pages and components.

## Files Created

### Core Components
- **`components/ui/confirmation-dialog.tsx`** - Main dialog component (140 lines)
- **`components/session/SessionActionBar.tsx`** - Example: Delete session with confirmation
- **`components/auth/LogoutButton.tsx`** - Example: Logout with confirmation

### Custom Hooks
- **`hooks/use-confirmation.ts`** - Generic confirmation dialog hook
- **`hooks/use-delete-session.ts`** - Session deletion hook with API integration
- **`hooks/use-logout.ts`** - Logout hook with auth context integration

### Documentation
- **`CONFIRMATION_DIALOG_GUIDE.md`** - Complete component documentation
- **`components/ConfirmationDialogDemo.tsx`** - Interactive examples (copy into route to demo)

## Integration Examples

### 1. Add Delete Button to Session Detail Page

**File:** `app/therapist/sessions/[id]/page.tsx`

Add this import at the top:

```tsx
import { SessionActionBar } from '@/components/session/SessionActionBar';
```

Add this JSX where you want the delete button (e.g., after the back button):

```tsx
{/* In the header section, after the back button */}
<SessionActionBar
  sessionId={id}
  patientName={patient?.name}
  sessionDate={formatDateTime(session.session_date)}
/>
```

### 2. Add Logout Button to Header/Navigation

**File:** `app/therapist/layout.tsx` or your header component

Add this import:

```tsx
import { LogoutButton } from '@/components/auth/LogoutButton';
```

Add the button in your navigation/header:

```tsx
<nav className="flex gap-4">
  {/* Other nav items */}
  <LogoutButton />
</nav>
```

Or use as a menu item:

```tsx
<LogoutButton variant="ghost" showIcon={true} />
```

### 3. Create Custom Destructive Action

For any destructive action (e.g., delete patient), use this pattern:

```tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

interface DeletePatientButtonProps {
  patientId: string;
  patientName: string;
}

export function DeletePatientButton({
  patientId,
  patientName
}: DeletePatientButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const response = await fetch(`/api/patients/${patientId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete patient');
      }

      // Redirect after successful deletion
      router.push('/therapist');
    } catch (error) {
      setIsDeleting(false);
      throw error;
    }
  };

  return (
    <>
      <Button
        variant="destructive"
        onClick={() => setShowConfirm(true)}
      >
        <Trash2 className="w-4 h-4 mr-2" />
        Delete Patient
      </Button>

      <ConfirmationDialog
        isOpen={showConfirm}
        onOpenChange={setShowConfirm}
        title={`Delete ${patientName}?`}
        description={`This will permanently delete ${patientName} and all associated sessions.`}
        warning="This action cannot be undone."
        onConfirm={handleDelete}
        confirmLabel="Delete Patient"
        cancelLabel="Keep Patient"
        variant="destructive"
        isDangerous={true}
        isLoading={isDeleting}
      />
    </>
  );
}
```

## Component API

### ConfirmationDialog Props

```typescript
interface ConfirmationDialogProps {
  // Required
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  onConfirm: () => void | Promise<void>;

  // Optional content
  description?: string;           // Secondary text explaining the action
  warning?: string;               // Warning text in highlighted box

  // Optional labels
  confirmLabel?: string;          // Default: "Confirm"
  cancelLabel?: string;           // Default: "Cancel"

  // Optional styling
  variant?: 'destructive' | 'default' | 'warning';  // Default: 'default'
  isDangerous?: boolean;          // Makes confirm button red (default: false)
  isLoading?: boolean;            // Shows spinner on confirm button
  disabled?: boolean;             // Disables all buttons

  // Optional callback
  onCancel?: () => void;          // Called when dialog is cancelled
}
```

## Variant Comparison

| Variant | Use Case | Icon Color | Button Color |
|---------|----------|-----------|--------------|
| `destructive` | Delete operations | Red | Red |
| `warning` | Important actions | Amber | Primary |
| `default` | Standard confirmations | Blue | Primary |

## Usage Patterns

### Pattern 1: Simple Confirmation

```tsx
const [showConfirm, setShowConfirm] = useState(false);

<Button onClick={() => setShowConfirm(true)}>Action</Button>

<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Confirm?"
  onConfirm={() => console.log('Done')}
/>
```

### Pattern 2: With Async Operation

```tsx
const [showConfirm, setShowConfirm] = useState(false);

const handleAsync = async () => {
  const response = await fetch('/api/action', { method: 'POST' });
  if (!response.ok) throw new Error('Failed');
};

<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Perform action?"
  onConfirm={handleAsync}  // Returns Promise
/>
```

### Pattern 3: Destructive with Warning

```tsx
<ConfirmationDialog
  isOpen={showConfirm}
  onOpenChange={setShowConfirm}
  title="Delete Item?"
  description="Delete 'Item Name'?"
  warning="This cannot be undone."
  onConfirm={handleDelete}
  variant="destructive"
  isDangerous={true}
  confirmLabel="Delete"
  cancelLabel="Keep"
/>
```

## Styling

The component uses Tailwind CSS variables from your theme. To customize:

Edit `app/globals.css`:

```css
:root {
  /* Destructive actions */
  --destructive: hsl(0, 84%, 60%);
  --destructive-foreground: hsl(0, 0%, 100%);

  /* Primary colors */
  --primary: hsl(217, 91%, 60%);
  --primary-foreground: hsl(0, 0%, 100%);
}
```

## Best Practices

### Do
✅ Use `variant="destructive"` for delete operations
✅ Include `warning` text explaining irreversible actions
✅ Use clear action verbs in labels ("Delete", "Logout", "Archive")
✅ Handle errors without closing the dialog
✅ Show loading state during async operations
✅ Test keyboard navigation (ESC to close, Enter to confirm)

### Don't
❌ Use confirmation dialogs for non-destructive actions
❌ Use unclear labels like "Yes" or "OK"
❌ Close dialog before async operation completes
❌ Ignore error messages from API calls
❌ Make dialogs hard to dismiss

## Accessibility

The component includes:
- ✅ Semantic HTML
- ✅ Keyboard navigation (ESC, Tab, Enter)
- ✅ Focus management
- ✅ ARIA labels
- ✅ High contrast colors
- ✅ Clear visual warnings

## Testing

Basic test example:

```tsx
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

test('shows dialog when isOpen is true', () => {
  render(
    <ConfirmationDialog
      isOpen={true}
      onOpenChange={() => {}}
      title="Test Dialog"
      onConfirm={() => {}}
    />
  );

  expect(screen.getByText('Test Dialog')).toBeInTheDocument();
});

test('calls onConfirm when confirm button is clicked', async () => {
  const user = userEvent.setup();
  const onConfirm = jest.fn();

  render(
    <ConfirmationDialog
      isOpen={true}
      onOpenChange={() => {}}
      title="Test"
      onConfirm={onConfirm}
    />
  );

  await user.click(screen.getByText('Confirm'));
  expect(onConfirm).toHaveBeenCalled();
});

test('closes dialog when ESC is pressed', async () => {
  const user = userEvent.setup();
  const onOpenChange = jest.fn();

  render(
    <ConfirmationDialog
      isOpen={true}
      onOpenChange={onOpenChange}
      title="Test"
      onConfirm={() => {}}
    />
  );

  await user.keyboard('{Escape}');
  expect(onOpenChange).toHaveBeenCalledWith(false);
});
```

## Common Issues & Solutions

### Dialog not showing
Check that `isOpen={true}` and `onOpenChange` is updating state.

### Loading state not showing
Ensure `onConfirm` returns a Promise: `async () => { ... }`

### Dialog closing too early
Don't manually close with `setShowConfirm(false)` during async operations.

### Styles not applying
Make sure Tailwind CSS is configured and styles are built.

## Next Steps

1. **Add to Session Detail Page**
   - Import `SessionActionBar`
   - Add to session header

2. **Add to Navigation**
   - Import `LogoutButton`
   - Add to header/layout

3. **Create Custom Dialogs**
   - Follow the `SessionActionBar` pattern
   - Use `ConfirmationDialog` component

4. **Test with Backend**
   - Ensure API endpoints return correct responses
   - Test error handling

5. **Iterate on UX**
   - Gather user feedback
   - Refine warning messages
   - Improve descriptions

## Support

For detailed documentation, see: `CONFIRMATION_DIALOG_GUIDE.md`

For component props and API: `components/ui/confirmation-dialog.tsx`

For examples: `components/session/SessionActionBar.tsx` or `components/auth/LogoutButton.tsx`
