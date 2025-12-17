# Branded Types for Type-Safe ID Handling

## Overview

The frontend now includes **branded types** for ID handling that prevent mixing different types of IDs at compile time. This adds a layer of type safety without any runtime cost.

## What Are Branded Types?

Branded types are a TypeScript pattern that creates distinct types from the same underlying type (in this case, `string`). Even though `PatientId`, `SessionId`, and `UserId` are all strings at runtime, TypeScript treats them as completely different types.

**Example of the problem this solves:**

```typescript
// Without branded types, this compiles fine but is wrong:
const patientId = "patient-123";
const sessionId = "session-456";

function fetchSession(id: string) {
  // Caller doesn't know what type of ID is expected
  // Easy to accidentally pass the wrong ID
}

fetchSession(patientId); // Runtime will fail if patientId is semantically wrong
```

**With branded types:**

```typescript
const patientId = createPatientId("patient-123");
const sessionId = createSessionId("session-456");

function fetchSession(id: SessionId) {
  // Type signature is clear about what's expected
}

fetchSession(patientId); // COMPILE ERROR - can't pass PatientId to SessionId
fetchSession(sessionId); // CORRECT - compiles and runs fine
```

## Available Types and Functions

### Branded Type Definitions

Located in `/lib/types.ts`:

- `PatientId` - Type for patient identifiers
- `SessionId` - Type for session identifiers
- `UserId` - Type for user/therapist identifiers

### Creator Functions

Create branded IDs from raw strings:

```typescript
import { createPatientId, createSessionId, createUserId } from '@/lib/types';

const patientId = createPatientId('patient-123');
const sessionId = createSessionId('session-456');
const userId = createUserId('user-789');
```

**Note:** Creator functions validate that the ID is not empty and throw an error if validation fails.

### Type Guard Functions

Check if a value is a valid branded type at runtime:

```typescript
import { isPatientId, isSessionId, isUserId } from '@/lib/types';

if (isPatientId(rawData.patient_id)) {
  // TypeScript now knows it's a PatientId
  console.log(rawData.patient_id); // type: PatientId
}
```

Useful when processing untrusted data from external sources.

### Unwrap Function

Extract the raw string from a branded type:

```typescript
import { unwrapId } from '@/lib/types';

const idString = unwrapId(patientId);
// Use in API calls:
fetch(`/api/patients/${idString}`);
```

## Usage Patterns

### In Function Signatures

```typescript
async function fetchPatientSessions(patientId: PatientId): Promise<Session[]> {
  const response = await fetch(`/api/patients/${unwrapId(patientId)}/sessions`);
  return response.json();
}

// Correct usage
const id = createPatientId('patient-123');
await fetchPatientSessions(id); // OK

// Wrong usage - won't compile
const sessionId = createSessionId('session-456');
await fetchPatientSessions(sessionId); // ERROR: Type mismatch
```

### In Data Structures

```typescript
interface SessionData {
  id: SessionId;
  patientId: PatientId;
  therapistId: UserId;
  title: string;
}

const session: SessionData = {
  id: createSessionId('session-abc'),
  patientId: createPatientId('patient-xyz'),
  therapistId: createUserId('user-doc'),
  title: 'Weekly Check-in',
};
```

### Processing Backend Responses

```typescript
function processSessionFromAPI(apiResponse: any): SessionData {
  return {
    id: createSessionId(apiResponse.id),
    patientId: createPatientId(apiResponse.patient_id),
    therapistId: createUserId(apiResponse.therapist_id),
    title: apiResponse.title,
  };
}
```

### With React Hooks

```typescript
function useSessionData(sessionId: SessionId) {
  // Hook implementation knows what type of ID it's working with
  return useSWR(`/api/sessions/${unwrapId(sessionId)}`, fetcher);
}

// Correct usage
const sessionId = createSessionId('session-456');
const { data } = useSessionData(sessionId); // OK

// Wrong usage
const patientId = createPatientId('patient-123');
const { data } = useSessionData(patientId); // ERROR: Type mismatch
```

## Best Practices

1. **Create branded IDs immediately upon receiving from backend:**
   ```typescript
   const patientId = createPatientId(apiResponse.id);
   ```

2. **Use branded types in all function signatures that accept IDs:**
   ```typescript
   // Good
   function process(patientId: PatientId) { }

   // Avoid
   function process(id: string) { }
   ```

3. **Keep IDs branded throughout the application:**
   - React component props
   - Hook parameters and return values
   - Context/state management
   - Data structures

4. **Unwrap only when necessary:**
   - API calls: `fetch(\`/api/../${unwrapId(id)}\`)`
   - Logging: `console.log(unwrapId(id))`
   - String interpolation: `` `ID: ${unwrapId(id)}` ``

5. **Use type guards for untrusted data:**
   ```typescript
   if (isSessionId(value)) {
     // Use value safely as SessionId
   }
   ```

6. **Never cast between different ID types unless semantically correct:**
   ```typescript
   // Usually wrong - avoid this pattern
   const userId = sessionId as UserId;

   // Only use if there's a documented reason
   ```

## Examples

Complete working examples can be found in `/lib/branded-id-examples.ts`. This file includes:

- Basic creation and type guards
- Function signatures with branded types
- Data structure patterns
- Array and collection operations
- Error handling patterns
- Integration with hooks
- Backend response processing

## Benefits

- **Compile-time Safety:** Catch ID mix-ups before runtime
- **Self-Documenting:** Clear from function signatures what type of ID is expected
- **Prevents Bugs:** Type checker prevents accidentally passing wrong ID types
- **Zero Runtime Cost:** Branded types compile away to regular strings
- **IDE Support:** Full autocomplete and type checking in editors

## Migration Guide

For existing code that uses plain strings for IDs:

1. Change function signatures to use branded types:
   ```typescript
   // Before
   function getSession(id: string) { }

   // After
   function getSession(id: SessionId) { }
   ```

2. Update callers to create branded IDs:
   ```typescript
   // Before
   getSession('session-123');

   // After
   getSession(createSessionId('session-123'));
   ```

3. Update state and prop types:
   ```typescript
   // Before
   const [patientId, setPatientId] = useState<string>('');

   // After
   const [patientId, setPatientId] = useState<PatientId | null>(null);
   ```

## References

- **Type Definitions:** `/lib/types.ts` (lines 1-118)
- **Examples:** `/lib/branded-id-examples.ts`
- **Related Utilities:** `/lib/type-utils.ts` (general TypeScript utilities)

## Questions?

If you encounter issues or need clarification:

1. Check `/lib/branded-id-examples.ts` for usage patterns
2. Review the JSDoc comments in `/lib/types.ts`
3. Consult the "Best Practices" section above
