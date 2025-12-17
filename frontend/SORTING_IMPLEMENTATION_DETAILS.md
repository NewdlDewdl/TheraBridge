# Sorting Controls - Implementation Details

## File Summary

### 1. `hooks/useSessionSort.ts` (2.6 KB)

**Purpose:** Manages sorting logic for session lists with memoization for performance.

**Key Features:**
- Supports three sort fields: `date`, `patient_name`, `status`
- Uses `useMemo` to prevent unnecessary recalculations
- Handles both ascending and descending order

**Usage Example:**
```tsx
const { sortConfig, setSortField, setSortOrder, sortedSessions, toggleSortOrder } = 
  useSessionSort(sessions, patientMap);

// Sort by date in descending order
setSortField('date');
setSortOrder('desc');

// Toggle between asc/desc
toggleSortOrder();
```

### 2. `hooks/usePatientSort.ts` (2.8 KB)

**Purpose:** Manages sorting logic for patient lists with stats integration.

**Key Features:**
- Supports three sort fields: `name`, `latest_session`, `total_sessions`
- Takes optional stats object for calculating latest_session and total_sessions
- Uses `useMemo` for performance optimization

**Usage Example:**
```tsx
const patientStats = {
  'patient-1': {
    totalSessions: 5,
    latestSessionDate: '2024-12-17',
    actionItems: 3,
    riskFlags: 0
  }
};

const { sortConfig, setSortField, sortedPatients } = 
  usePatientSort(patients, patientStats);
```

### 3. `components/SessionSortControl.tsx` (2.2 KB)

**Purpose:** UI component for session sorting with dropdown and toggle button.

**Layout:**
```
[Sort: ] [Date ▼] [↓ Newest First]
```

**Features:**
- Dropdown to select sort field (Date, Patient Name, Status)
- Button to toggle sort order
- Icon indicates current sort direction
- Label updates based on sort field

**Responsive:** Uses `flex items-center gap-2`

### 4. `components/PatientSortControl.tsx` (2.3 KB)

**Purpose:** UI component for patient sorting with dropdown and toggle button.

**Layout:**
```
[Sort: ] [Patient Name ▼] [↑ A-Z]
```

**Features:**
- Dropdown to select sort field (Patient Name, Latest Session, Total Sessions)
- Button to toggle sort order
- Icon indicates current sort direction
- Dynamic labels based on context

## Integration Examples

### Therapist Dashboard

```tsx
// Import the hook and component
import { usePatientSort } from '@/hooks/usePatientSort';
import { PatientSortControl } from '@/components/PatientSortControl';

// In component:
const { sortConfig, setSortField, setSortOrder, sortedPatients, toggleSortOrder } =
  usePatientSort(patients, patientStats);

// In render:
<div className="flex items-center justify-end">
  <PatientSortControl
    sortField={sortConfig.field}
    sortOrder={sortConfig.order}
    onSortFieldChange={setSortField}
    onSortOrderChange={setSortOrder}
    onToggleSortOrder={toggleSortOrder}
  />
</div>

<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
  {sortedPatients.map((patient) => (
    // Patient card
  ))}
</div>
```

### Patient Detail Page

```tsx
// Import the hook and component
import { useSessionSort } from '@/hooks/useSessionSort';
import { SessionSortControl } from '@/components/SessionSortControl';

// In component:
const patientMap = patient ? { [patient.id]: patient.name } : {};
const {
  sortConfig,
  setSortField,
  setSortOrder,
  sortedSessions,
  toggleSortOrder,
} = useSessionSort(sessions, patientMap);

// Apply sorting after filters and search
const displaySessions = getFilteredSessions().sort((a, b) => {
  // Sort logic based on sortConfig
});

// In render:
<div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
  <SessionSearchInput {...searchProps} />
  <SessionSortControl
    sortField={sortConfig.field}
    sortOrder={sortConfig.order}
    onSortFieldChange={setSortField}
    onSortOrderChange={setSortOrder}
    onToggleSortOrder={toggleSortOrder}
  />
</div>

<div className="grid gap-4">
  {displaySessions.map((session) => (
    <SessionCard key={session.id} session={session} />
  ))}
</div>
```

## Sort Order Labels

### Session Sorting
- **Date**:
  - Ascending: "Oldest First"
  - Descending: "Newest First" (default)

- **Patient Name**:
  - Ascending: "A-Z"
  - Descending: "Z-A"

- **Status**:
  - Ascending: "A-Z"
  - Descending: "Z-A"

### Patient Sorting
- **Patient Name**:
  - Ascending: "A-Z" (default)
  - Descending: "Z-A"

- **Latest Session**:
  - Ascending: "Oldest First"
  - Descending: "Newest First"

- **Total Sessions**:
  - Ascending: "Least"
  - Descending: "Most"

## Type Definitions

```tsx
// Session Sort Types
export type SortField = 'date' | 'patient_name' | 'status';
export type SortOrder = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  order: SortOrder;
}

// Patient Sort Types
export type PatientSortField = 'name' | 'latest_session' | 'total_sessions';

export interface PatientSortConfig {
  field: PatientSortField;
  order: SortOrder;
}

export interface PatientStats {
  totalSessions: number;
  latestSessionDate?: string;
  actionItems: number;
  riskFlags: number;
}
```

## Sorting Algorithm Details

### Date Sorting
```ts
new Date(a.session_date).getTime() - new Date(b.session_date).getTime()
```

### String Sorting (Name, Status)
```ts
a.name.localeCompare(b.name)  // Handles internationalization
```

### Numeric Sorting (Total Sessions)
```ts
sessionsA - sessionsB
```

## Performance Considerations

1. **memoization**: Sort computation uses `useMemo` with dependencies:
   ```ts
   const sortedSessions = useMemo(() => {
     // Sort logic
   }, [sessions, sortConfig, patientMap]);
   ```

2. **Dependency Array**: Optimized to prevent unnecessary re-sorts
   - Includes: `sessions`, `sortConfig`, `patientMap`
   - Excludes: Unrelated state changes

3. **No Network Calls**: All sorting is client-side
   - Instant user feedback
   - No server round-trip required

## Accessibility

- Sort control button has title attribute for hover tooltip
- Uses semantic HTML (`<select>` equivalent via Radix UI)
- Clear visual indicator of sort direction (arrow icon)
- Keyboard navigable via native select component

## Browser Compatibility

- Uses standard `Array.sort()` method
- `localeCompare()` for string comparison (all modern browsers)
- `Date` and `getTime()` (all browsers)
- No polyfills required

## Testing Recommendations

```tsx
// Example test cases
describe('useSessionSort', () => {
  it('should sort sessions by date descending by default', () => {
    const { result } = renderHook(() => useSessionSort(sessions));
    expect(result.current.sortConfig.field).toBe('date');
    expect(result.current.sortConfig.order).toBe('desc');
  });

  it('should update sort field', () => {
    const { result } = renderHook(() => useSessionSort(sessions));
    act(() => {
      result.current.setSortField('status');
    });
    expect(result.current.sortConfig.field).toBe('status');
  });

  it('should toggle sort order', () => {
    const { result } = renderHook(() => useSessionSort(sessions));
    act(() => {
      result.current.toggleSortOrder();
    });
    expect(result.current.sortConfig.order).toBe('asc');
  });
});
```
