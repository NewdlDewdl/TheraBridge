# Sorting Controls Implementation

This document describes the sorting controls added to the therapist dashboard.

## Overview

Two separate sorting systems have been implemented:
1. **Patient Sorting** - Sort the list of patients on the main therapist dashboard
2. **Session Sorting** - Sort sessions within a patient's detail view

## Components

### SessionSortControl (`components/SessionSortControl.tsx`)

UI component for sorting sessions with a dropdown and toggle button.

**Props:**
- `sortField: 'date' | 'patient_name' | 'status'` - Current sort field
- `sortOrder: 'asc' | 'desc'` - Current sort order
- `onSortFieldChange: (field) => void` - Callback when sort field changes
- `onSortOrderChange: (order) => void` - Callback when sort order changes
- `onToggleSortOrder?: () => void` - Optional callback for toggle

**Sort Fields:**
- `date` - Session date (Newest/Oldest first)
- `patient_name` - Patient name (A-Z/Z-A)
- `status` - Session status (A-Z/Z-A)

**Example Usage:**
```tsx
<SessionSortControl
  sortField="date"
  sortOrder="desc"
  onSortFieldChange={setSortField}
  onSortOrderChange={setSortOrder}
/>
```

### PatientSortControl (`components/PatientSortControl.tsx`)

UI component for sorting patients with a dropdown and toggle button.

**Props:**
- `sortField: 'name' | 'latest_session' | 'total_sessions'` - Current sort field
- `sortOrder: 'asc' | 'desc'` - Current sort order
- `onSortFieldChange: (field) => void` - Callback when sort field changes
- `onSortOrderChange: (order) => void` - Callback when sort order changes
- `onToggleSortOrder?: () => void` - Optional callback for toggle

**Sort Fields:**
- `name` - Patient name (A-Z/Z-A)
- `latest_session` - Latest session date (Newest/Oldest first)
- `total_sessions` - Number of sessions (Most/Least)

**Example Usage:**
```tsx
<PatientSortControl
  sortField="name"
  sortOrder="asc"
  onSortFieldChange={setSortField}
  onSortOrderChange={setSortOrder}
/>
```

## Hooks

### useSessionSort (`hooks/useSessionSort.ts`)

React hook for managing session sorting logic.

**Returns:**
```ts
{
  sortConfig: SortConfig;              // Current sort configuration
  setSortField: (field) => void;       // Update sort field
  setSortOrder: (order) => void;       // Update sort order
  sortedSessions: Session[];           // Sorted sessions array
  toggleSortOrder: () => void;         // Toggle between asc/desc
}
```

**Example Usage:**
```ts
const { sortConfig, setSortField, sortedSessions } = useSessionSort(
  sessions,
  patientMap  // Optional: for 'patient_name' sorting
);
```

### usePatientSort (`hooks/usePatientSort.ts`)

React hook for managing patient sorting logic.

**Returns:**
```ts
{
  sortConfig: PatientSortConfig;       // Current sort configuration
  setSortField: (field) => void;       // Update sort field
  setSortOrder: (order) => void;       // Update sort order
  sortedPatients: Patient[];           // Sorted patients array
  toggleSortOrder: () => void;         // Toggle between asc/desc
}
```

**Example Usage:**
```ts
const { sortConfig, setSortField, sortedPatients } = usePatientSort(
  patients,
  patientStats  // Optional: stats map for latest_session and total_sessions
);
```

## Integration Points

### Therapist Dashboard (`app/therapist/page.tsx`)

- `PatientSortControl` appears in the top-right corner above patient cards
- Integrated with `usePatientSort` hook
- Stats are pre-calculated for each patient and passed to the sort hook
- Responsive layout: sort control stacks on mobile, appears inline on desktop

### Patient Detail Page (`app/therapist/patients/[id]/page.tsx`)

- `SessionSortControl` appears alongside the search input in a flex container
- Integrated with `useSessionSort` hook
- Works seamlessly with existing `SessionFilters` and search functionality
- Sort order is applied after filters and search are evaluated
- Patient name sorting uses the current patient from the page context

## Features

### Visual Feedback

- **Sort Direction Icon**: Arrow up (↑) for ascending, arrow down (↓) for descending
- **Dynamic Labels**: Labels change based on the sort field:
  - Date: "Newest First" / "Oldest First"
  - Patient Name: "A-Z" / "Z-A"
  - Status: "A-Z" / "Z-A"
  - Total Sessions: "Most" / "Least"

### Responsive Design

- **Mobile**: Controls stack vertically
- **Tablet/Desktop**: Controls appear side-by-side with search
- Uses Tailwind CSS responsive classes (`md:flex-row`, `md:items-center`, etc.)

### Performance

- `useMemo` used in sorting hooks to prevent unnecessary re-sorts
- Dependency arrays optimized to trigger only when data changes
- Client-side sorting (no network requests)

## Type Safety

The implementation uses TypeScript with branded types for sort fields:

```ts
export type SortField = 'date' | 'patient_name' | 'status';
export type PatientSortField = 'name' | 'latest_session' | 'total_sessions';
```

This prevents passing invalid sort field values at compile time.

## Integration with Existing Features

### Search and Sorting

On the patient detail page, sorting works in conjunction with search:
1. Search filters sessions by transcript content
2. Filters narrow by status and date range
3. Sorting is applied to the final filtered results

### Maintaining State

Sort state is managed locally in the component using React hooks. The state is preserved as long as the component is mounted. Refreshing the page resets sort to defaults.

## Future Enhancements

Potential improvements for future iterations:
1. **Persistence**: Save sort preferences to localStorage
2. **Default Preferences**: Allow users to set preferred sort order
3. **Multi-level Sorting**: Sort by multiple fields (e.g., status then date)
4. **Saved Views**: Save custom sort + filter combinations
5. **Export**: Export sorted data to CSV/Excel
