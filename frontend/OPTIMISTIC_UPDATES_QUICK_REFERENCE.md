# Optimistic Updates - Quick Reference

## TL;DR

Use these hooks to make your UI feel instant:

```typescript
// Single session
const { session, mutate } = useOptimisticSession(sessionId);

// Session list
const { sessions, mutate } = useOptimisticSessions({ patientId });

// File upload
const { uploadAndOptimize, progress } = useOptimisticUpload({
  onOptimisticSessionCreated: (s) => mutate(ss => [...ss, s]),
  onUploadComplete: (s) => { /* already showing */ }
});
```

## Import Statements

```typescript
// Hooks
import { useOptimisticSession } from '@/hooks/useOptimisticSession';
import { useOptimisticSessions } from '@/hooks/useOptimisticSessions';
import { useOptimisticUpload } from '@/hooks/useOptimisticUpload';

// Component
import { SessionUploaderOptimistic } from '@/components/SessionUploaderOptimistic';

// Testing
import { createMockSession, testOptimisticFlow } from '@/lib/optimistic-test-utils';
```

## Hook Patterns

### Pattern 1: Update Single Item
```typescript
const { session, mutate } = useOptimisticSession(id);

// UI updates immediately, reverts on error
await mutate({ ...session, status: 'processed' });
```

### Pattern 2: Update List
```typescript
const { sessions, mutate } = useOptimisticSessions({ patientId });

// Add
await mutate(ss => [...ss, newSession]);

// Remove
await mutate(ss => ss.filter(s => s.id !== idToRemove));

// Update one
await mutate(ss => ss.map(s => s.id === id ? updated : s));

// Batch update
await mutate(ss => ss.map(s => ({ ...s, status: 'processed' })));
```

### Pattern 3: Upload with Progress
```typescript
const { uploadAndOptimize, progress, isUploading } = useOptimisticUpload({
  onOptimisticSessionCreated: (session) => {
    // Show immediately
    sessionsMutate(ss => [...ss, session]);
  },
  onUploadComplete: (session) => {
    // Replace optimistic with real
    sessionsMutate(ss => ss.map(s => s.id.startsWith('temp-') ? session : s));
  }
});

await uploadAndOptimize(patientId, file);
```

## Common Operations

### Optimistic Create
```typescript
// Show new session immediately
const optimisticSession = { id: 'temp-1', status: 'uploading', ... };
await mutate(ss => [...ss, optimisticSession], { revalidate: false });

// Upload file in background, replace on success
const real = await uploadSession(patientId, file);
await mutate(ss => ss.map(s => s.id === 'temp-1' ? real : s));
```

### Optimistic Update
```typescript
// Show updated status immediately
await mutate(
  { ...session, status: 'processed' },
  { revalidate: true } // Confirm with server
);
```

### Optimistic Delete
```typescript
// Remove immediately
await mutate(ss => ss.filter(s => s.id !== toDelete));
// Reverts automatically if API fails
```

## Error Handling

Errors are handled automatically:
```typescript
try {
  // This works even if API fails
  await mutate(optimisticData);
  // UI already reverted if there was an error
} catch (error) {
  // This only for logging
  console.error('Operation failed:', error);
}
```

## Options

### useOptimisticSession Options
```typescript
useOptimisticSession(sessionId, {
  refreshInterval: 5000 // ms, defaults to auto
})
```

### useOptimisticSessions Options
```typescript
useOptimisticSessions({
  patientId: 'p-123',           // Filter
  status: 'processed',          // Filter by status
  refreshInterval: 30000        // ms, defaults to auto
})
```

### Mutate Options
```typescript
await mutate(newData, {
  revalidate: true,             // Confirm with server (default)
  rollbackOnError: true         // Auto-revert on error (default)
})
```

### useOptimisticUpload Options
```typescript
useOptimisticUpload({
  onOptimisticSessionCreated: (session) => {},  // Called immediately
  onUploadComplete: (session) => {},            // Called on success
  onUploadError: (error) => {}                  // Called on error
})
```

## State Properties

### useOptimisticSession Return
```typescript
{
  session: Session | undefined,        // The data
  data: Session | undefined,           // Alias for session
  isLoading: boolean,                  // Currently fetching
  isError: boolean,                    // Error occurred
  error: ApiError | undefined,         // Error object
  isProcessing: boolean,               // Session still processing
  mutate: (data) => Promise,           // Update with optimistic
  refresh: () => Promise                // Manual refresh
}
```

### useOptimisticSessions Return
```typescript
{
  sessions: Session[] | undefined,     // The data
  data: Session[] | undefined,         // Alias
  isLoading: boolean,
  isError: boolean,
  error: ApiError | undefined,
  mutate: (data) => Promise,           // Update with optimistic
  refresh: () => Promise
}
```

### useOptimisticUpload Return
```typescript
{
  isUploading: boolean,                // Currently uploading
  progress: number,                    // 0-100%
  error: string | null,                // Error message
  optimisticSession: Session | null,   // Temp session
  uploadAndOptimize: (patientId, file) => Promise<Session>,
  reset: () => void                    // Clear state
}
```

## Testing

```typescript
import { createMockSession, testOptimisticFlow } from '@/lib/optimistic-test-utils';

// Create test data
const session = createMockSession({ status: 'uploading' });

// Test optimistic flow
const result = await testOptimisticFlow({
  initial: session,
  optimistic: { ...session, status: 'processing' },
  final: { ...session, status: 'processed' }
});

// Assert what changed
assertOptimisticUpdate({
  before: session,
  after: updatedSession,
  changed: ['status'],
  unchanged: ['id', 'patient_id']
});
```

## Real-World Example: Session Uploader

```typescript
export function PatientPage({ patientId }: Props) {
  const { sessions, mutate: sessionsMutate } = useOptimisticSessions({ patientId });
  const { uploadAndOptimize, progress } = useOptimisticUpload({
    onOptimisticSessionCreated: (opt) => {
      sessionsMutate(ss => [...ss, opt], { revalidate: false });
    },
    onUploadComplete: (real) => {
      sessionsMutate(
        ss => ss.map(s => s.id.startsWith('temp-') ? real : s),
        { revalidate: false }
      );
    }
  });

  return (
    <div>
      <SessionUploaderOptimistic
        patientId={patientId}
        onUploadComplete={(id) => router.push(`/sessions/${id}`)}
      />
      <SessionList sessions={sessions} />
    </div>
  );
}
```

## Checklist: Adding Optimistic Updates

- [ ] Import hook: `import { useOptimistic* } from '@/hooks'`
- [ ] Call hook with options
- [ ] Handle optimistic mutation: `await mutate(newData)`
- [ ] Test with slow network (DevTools Network tab)
- [ ] Verify UI updates immediately
- [ ] Verify rollback on network error

## Performance Tips

1. Use `revalidate: false` for cosmetic changes
2. Use `revalidate: true` for critical data
3. Don't poll constantly - let SWR manage it
4. Test with throttled network (DevTools → Network)

## Debugging

### See all mutations
```typescript
const tracker = createMutationTracker();
tracker.track(data);
console.log(tracker.getMutations());
```

### Simulate slow network
```typescript
await simulateSlowNetwork(apiCall, {
  latency: 5000,
  packetLoss: 0.1
});
```

### Mock API for testing
```typescript
const { mutate } = createMockSWRMutate(initialData);
mutate.setShouldFail(true); // Simulate error
```

## Key Takeaways

✅ **Automatic rollback** - No manual error cleanup needed
✅ **Type-safe** - Full TypeScript support
✅ **Real-time feedback** - Progress bars, status updates
✅ **Works offline** - Retries automatically when online
✅ **Simple API** - Just `await mutate(newData)`

## Resources

- **Full Guide**: [OPTIMISTIC_UPDATES_GUIDE.md](./OPTIMISTIC_UPDATES_GUIDE.md)
- **Code Examples**: [OPTIMISTIC_UPDATES_EXAMPLES.tsx](./OPTIMISTIC_UPDATES_EXAMPLES.tsx)
- **Implementation Details**: [OPTIMISTIC_UPDATES_IMPLEMENTATION.md](./OPTIMISTIC_UPDATES_IMPLEMENTATION.md)
- **SWR Docs**: https://swr.vercel.app/
