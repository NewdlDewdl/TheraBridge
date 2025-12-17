# Optimistic UI Updates Guide

This guide explains how to implement optimistic UI updates in the PeerBridge frontend using SWR's `optimisticData` pattern.

## Overview

Optimistic updates make the UI feel responsive by immediately reflecting user actions before the server confirms them. If the operation fails, SWR automatically reverts the optimistic data back to the previous state.

**Benefits:**
- Better perceived performance and responsiveness
- Reduced perceived latency (especially on slow networks)
- Automatic error rollback with no manual cleanup needed
- Works seamlessly with SWR's caching and state management

## Core Concept

```typescript
// Before: User clicks button → waits for server → UI updates
// After:  User clicks button → UI updates immediately → server confirms/reverts
```

## Hooks Available

### 1. `useOptimisticSession` - Single Session Updates

Fetch and update a single session with optimistic changes that immediately reflect in the UI.

```typescript
import { useOptimisticSession } from '@/hooks/useOptimisticSession';

export function SessionDetailPage({ sessionId }: { sessionId: string }) {
  const { session, mutate, isProcessing } = useOptimisticSession(sessionId);

  const handleStatusUpdate = async (newStatus: SessionStatus) => {
    // Update UI immediately with optimistic data
    await mutate(
      { ...session, status: newStatus },
      { revalidate: true } // Revalidate after mutation completes
    );

    // If the API call succeeds, the UI already shows the new status
    // If it fails, SWR automatically reverts to the previous state
  };

  return (
    <div>
      {session && (
        <>
          <h1>{session.id}</h1>
          <p>Status: {session.status}</p>
          {isProcessing && <Spinner />}
        </>
      )}
    </div>
  );
}
```

**Key Features:**
- Automatically polls every 5 seconds while session is processing
- Optimistic mutations with automatic rollback on error
- Intelligent refresh interval based on session status
- Type-safe session updates

### 2. `useOptimisticSessions` - List Updates

Fetch and update a list of sessions with optimistic changes.

```typescript
import { useOptimisticSessions } from '@/hooks/useOptimisticSessions';

export function PatientSessionsPage({ patientId }: { patientId: string }) {
  const { sessions, mutate } = useOptimisticSessions({ patientId });

  const handleAddSession = async (newSession: Session) => {
    // Immediately add to list (optimistic)
    await mutate(
      (currentSessions) => [...(currentSessions || []), newSession],
      { revalidate: true }
    );
  };

  return (
    <div>
      {sessions?.map((session) => (
        <SessionCard key={session.id} session={session} />
      ))}
    </div>
  );
}
```

**Key Features:**
- Supports filtering by patient ID and status
- Optimistic array mutations with functional updates
- Automatic polling for in-progress sessions
- Type-safe session list operations

### 3. `useOptimisticUpload` - File Upload with Immediate Feedback

Handle file uploads with optimistic session creation and real-time progress.

```typescript
import { useOptimisticUpload } from '@/hooks/useOptimisticUpload';

export function UploadComponent({ patientId }: { patientId: string }) {
  const { isUploading, progress, error, uploadAndOptimize } = useOptimisticUpload({
    onOptimisticSessionCreated: (optimisticSession) => {
      // Called immediately when file starts uploading
      console.log('Optimistic session:', optimisticSession);
      // Add to UI immediately
    },
    onUploadComplete: (realSession) => {
      // Called when upload finishes and real data arrives
      console.log('Real session:', realSession);
      // Already showing in UI from optimistic update
    },
    onUploadError: (error) => {
      // Called on upload failure
      console.error('Upload failed:', error);
      // UI automatically reverts to previous state
    },
  });

  const handleFileSelect = async (file: File) => {
    await uploadAndOptimize(patientId, file);
  };

  return (
    <div>
      {isUploading && <ProgressBar value={progress} />}
      {error && <ErrorMessage message={error} />}
      <input type="file" onChange={(e) => handleFileSelect(e.target.files?.[0]!)} />
    </div>
  );
}
```

**Key Features:**
- Creates optimistic session immediately
- Provides real-time upload progress (0-100%)
- Automatic error handling and rollback
- Separate callbacks for each lifecycle event

## Complete Example: Enhanced Session Uploader

The `SessionUploaderOptimistic` component demonstrates all three patterns in action:

```typescript
import { SessionUploaderOptimistic } from '@/components/SessionUploaderOptimistic';

export function PatientDashboard() {
  return (
    <SessionUploaderOptimistic
      patientId="patient-123"
      onUploadComplete={(sessionId) => {
        // Navigate to newly uploaded session
      }}
    />
  );
}
```

**What happens:**
1. User selects file
2. `useOptimisticUpload` creates optimistic session immediately
3. Optimistic session added to list via `useOptimisticSessions`
4. Upload progress displays in real-time (10% → 100%)
5. Real session arrives from backend
6. Optimistic session replaced with real one
7. On error: optimistic session removed, error shown, user can retry

## Advanced Patterns

### Pattern 1: Optimistic Create with Fallback

```typescript
const { sessions, mutate } = useOptimisticSessions({ patientId });

const createSessionOptimistically = async (file: File) => {
  // Create temporary ID that looks real
  const tempId = `temp-${Date.now()}`;

  const optimisticSession: Session = {
    id: tempId,
    patient_id: patientId,
    status: 'uploading',
    // ... other fields
  };

  // Show immediately
  await mutate(
    (sessions) => [...(sessions || []), optimisticSession],
    { revalidate: false } // Don't revalidate yet - wait for real data
  );

  try {
    const realSession = await uploadSession(patientId, file);

    // Replace optimistic with real
    await mutate(
      (sessions) =>
        (sessions || []).map((s) => (s.id === tempId ? realSession : s)),
      { revalidate: false }
    );

    return realSession;
  } catch (error) {
    // Error automatically reverts optimistic session via SWR
    throw error;
  }
};
```

### Pattern 2: Optimistic Update with Rollback

```typescript
const { session, mutate } = useOptimisticSession(sessionId);

const updateSessionStatus = async (newStatus: SessionStatus) => {
  const previousSession = session;

  // Show new status immediately
  await mutate(
    { ...session, status: newStatus },
    { revalidate: true } // Revalidate to confirm with server
  );

  // If revalidate fails, SWR automatically uses previousSession
  // No manual error handling needed!
};
```

### Pattern 3: Optimistic Delete

```typescript
const { sessions, mutate } = useOptimisticSessions({ patientId });

const deleteSessionOptimistically = async (sessionId: string) => {
  const previousSessions = sessions;

  // Remove immediately from UI
  await mutate(
    (sessions) => (sessions || []).filter((s) => s.id !== sessionId),
    {
      optimisticData: (sessions) =>
        (sessions || []).filter((s) => s.id !== sessionId),
      rollbackOnError: true,
      revalidate: false,
    }
  );

  try {
    await deleteSessionAPI(sessionId);
    // Confirmed by server - no action needed
  } catch (error) {
    // Error automatically reverts to previousSessions
    throw error;
  }
};
```

## SWR Configuration

All optimistic hooks use these SWR configuration defaults:

```typescript
{
  // Automatic rollback if API call fails
  rollbackOnError: true,

  // Don't refocus on window focus (prevent unwanted revalidations)
  revalidateOnFocus: false,

  // Revalidate when network comes back online
  revalidateOnReconnect: true,

  // Deduplication interval - prevent duplicate requests
  dedupingInterval: 120000, // 2 minutes

  // Dynamic refresh based on data state
  refreshInterval: (data) => {
    // Poll while processing, stop when complete
    return data?.status === 'processing' ? 5000 : 0;
  }
}
```

## Error Handling

SWR handles errors automatically with the `rollbackOnError: true` option:

```typescript
const { sessions, mutate } = useOptimisticSessions();

try {
  // UI updates immediately
  await mutate(optimisticData, {
    optimisticData: optimisticData,
    rollbackOnError: true, // Automatic rollback!
    revalidate: true,
  });

  // If we reach here, the server confirmed the change
  console.log('Success - data is accurate');
} catch (error) {
  // If error occurs, the UI has ALREADY been reverted
  // This is just for logging/notifications
  console.error('Operation failed:', error);
}
```

## Performance Considerations

### 1. Disable Revalidation for Cosmetic Changes

```typescript
// Just updating UI, don't need server confirmation
await mutate(optimisticData, { revalidate: false });
```

### 2. Enable Revalidation for Critical Data

```typescript
// Need server confirmation for data integrity
await mutate(optimisticData, { revalidate: true });
```

### 3. Use Deduplication to Prevent Storms

```typescript
// All hooks use 120s deduplication by default
// This prevents multiple requests for the same endpoint within 2 minutes
const { sessions } = useOptimisticSessions({
  patientId, // endpoint: /api/sessions?patient_id=...
  // deduplication interval prevents redundant requests
});
```

## Testing Optimistic Updates

### Test Immediate UI Update

```typescript
test('optimistic update shows immediately', async () => {
  const { result } = renderHook(() =>
    useOptimisticSession('session-123')
  );

  // Initial state
  expect(result.current.session?.status).toBe('uploading');

  // Trigger optimistic update
  await act(async () => {
    await result.current.mutate({
      ...result.current.session,
      status: 'processed',
    });
  });

  // UI updates immediately
  expect(result.current.session?.status).toBe('processed');
});
```

### Test Rollback on Error

```typescript
test('optimistic update reverts on error', async () => {
  // Mock API to fail
  mockAPI.delete.mockRejectedValue(new Error('Server error'));

  const { result } = renderHook(() =>
    useOptimisticSessions({ patientId: 'p1' })
  );

  const originalSessions = result.current.sessions;

  // Trigger delete
  await act(async () => {
    await result.current.mutate(
      (sessions) => sessions?.filter((s) => s.id !== 'session-1')
    );
  });

  // Session temporarily removed
  expect(result.current.sessions?.length).toBeLessThan(
    originalSessions?.length!
  );

  // After error, automatically reverts
  await waitFor(() => {
    expect(result.current.sessions).toEqual(originalSessions);
  });
});
```

## Migration Guide

### From Old SessionUploader to SessionUploaderOptimistic

**Before:**
```typescript
<SessionUploader patientId="p1" />
```

**After:**
```typescript
<SessionUploaderOptimistic patientId="p1" />
```

No other code changes needed - the new component handles all optimistic updates internally.

### From useSession to useOptimisticSession

**Before:**
```typescript
const { session, refresh } = useSession(sessionId);

// Manual handle of optimistic state needed
```

**After:**
```typescript
const { session, mutate } = useOptimisticSession(sessionId);

// Optimistic mutations with automatic rollback
await mutate(updatedSession);
```

## Best Practices

1. **Always provide visual feedback**: Show progress, loading state, or success indication
2. **Use rollbackOnError**: Let SWR handle error recovery automatically
3. **Revalidate for critical data**: Use `revalidate: true` for important state changes
4. **Skip revalidation for cosmetic changes**: Use `revalidate: false` for UI-only updates
5. **Handle specific errors**: Wrap mutations in try-catch for error notifications
6. **Test both success and failure**: Ensure UI handles both paths correctly

## Troubleshooting

### UI not updating optimistically

**Check:**
- Is `mutate` being called?
- Are you passing `optimisticData`?
- Is the hook mounted when mutation triggers?

### Changes not persisting after revalidate

**Check:**
- Did the API call actually succeed?
- Check network tab for failed requests
- Verify error boundaries aren't hiding errors

### Rollback happening unexpectedly

**Check:**
- Are you using `rollbackOnError: true`?
- Is the API endpoint returning an error status?
- Check console for error details

## Resources

- [SWR Documentation](https://swr.vercel.app/)
- [SWR Mutation](https://swr.vercel.app/docs/mutation)
- [Optimistic UI Patterns](https://swr.vercel.app/docs/mutation#optimistic-data)
