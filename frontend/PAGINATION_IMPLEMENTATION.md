# Pagination Implementation for Therapist Dashboard

## Overview
Comprehensive pagination system has been implemented for the TherapyBridge frontend, providing efficient data display across session lists and patient lists on the therapist dashboard.

## Components Created

### 1. Pagination Component (`components/ui/pagination.tsx`)
A reusable React component that displays pagination controls with the following features:

**Features:**
- **Page Number Buttons**: Shows 5 visible page numbers with ellipsis (...) for navigation
- **Previous/Next Buttons**: Chevron buttons to navigate between pages
- **Page Size Selector**: Dropdown to choose items per page (10, 25, 50, 100)
- **Item Counter**: Displays "Showing X to Y of Z items"
- **Smart Page Display**: Automatically centers current page in the visible range

**Props:**
```typescript
interface PaginationProps {
  currentPage: number;              // Current page number (1-indexed)
  totalPages: number;               // Total number of pages
  pageSize: number;                 // Items displayed per page
  totalItems: number;               // Total number of items
  onPageChange: (page: number) => void;        // Page change handler
  onPageSizeChange: (size: number) => void;    // Page size change handler
  pageSizeOptions?: number[];       // Available page size options (default: [10, 25, 50, 100])
  className?: string;               // Optional CSS class
}
```

**Design:**
- Uses Lucide React icons (ChevronLeft, ChevronRight, MoreHorizontal)
- Integrates with existing Button and Select components
- Responsive layout with flexbox
- Tailwind CSS styling matching project theme

### 2. usePagination Hook (`hooks/usePagination.ts`)
Custom React hook for managing pagination state and logic.

**Features:**
- Automatic page size calculations
- Safe page bounds checking
- Utilities to jump to first/last page
- Integration with TypeScript for type safety

**Returns:**
```typescript
interface UsePaginationResult<T> {
  currentPage: number;              // Current page (1-indexed)
  pageSize: number;                 // Items per page
  totalPages: number;               // Calculated total pages
  paginatedItems: T[];              // Sliced array of items for current page
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  goToFirstPage: () => void;        // Jump to page 1
  goToLastPage: () => void;         // Jump to last page
}
```

## Integration Points

### 1. Therapist Dashboard (`app/therapist/page.tsx`)
**What it paginates:** Patient list

**Configuration:**
- Initial page size: 9 patients per page (3x3 grid layout)
- Page size options: [9, 18, 27, 36] (matching grid multiples)
- Shows pagination when total patients > 9
- Preserves sorting controls above pagination

**Implementation:**
```typescript
const {
  currentPage,
  pageSize,
  totalPages,
  paginatedItems: paginatedPatients,
  onPageChange,
  onPageSizeChange,
} = usePagination(sortedPatients || [], { initialPageSize: 9 });
```

**Layout:**
- Pagination centered below the patient grid
- Conditional rendering (only shows if more than pageSize items)
- Maintains spacing consistency with existing design

### 2. Patient Detail Page (`app/therapist/patients/[id]/page.tsx`)
**What it paginates:** Session list for individual patient

**Configuration:**
- Initial page size: 10 sessions per page
- Page size options: [10, 25, 50, 100]
- Shows pagination when filtered sessions > 10
- Works seamlessly with search and sorting

**Implementation:**
```typescript
const {
  currentPage,
  pageSize,
  totalPages,
  paginatedItems: paginatedSessions,
  onPageChange,
  onPageSizeChange,
} = usePagination(displaySessions, { initialPageSize: 10 });
```

**Filtering Integration:**
- Pagination applies AFTER search and sort filters
- Page 1 resets when changing page size
- Maintains filter state across pagination

## User Experience Features

### Smart Page Number Display
- Shows up to 5 page numbers at a time
- Centers current page when possible
- Shows first and last pages with ellipsis for large page counts
- Example: "1 ... 3 4 5 6 7 ... 20" when on page 5 of 20

### Item Counter
- Always shows "Showing X to Y of Z items"
- Updates automatically when page size changes
- Accounts for partial last pages

### Page Size Selection
- Dropdown selector (Select component from existing UI library)
- Automatic page 1 reset on change
- Prevents API over-fetching

### Accessibility
- Semantic HTML with proper button roles
- Screen reader text for icon-only buttons ("Previous page", "Next page")
- Proper disabled states on boundary pages
- Keyboard accessible through existing Button component

## Technical Details

### State Management
- Uses React hooks (useState, useMemo)
- No external state management library required
- Integrates with existing component patterns

### Performance
- Efficient array slicing with useMemo
- No unnecessary re-renders due to proper memoization
- Works with all array types through TypeScript generics

### Styling
- Uses project's Tailwind CSS configuration
- Respects dark mode via muted-foreground classes
- Icon sizing matches existing design patterns
- Gap and padding aligned with project standards

## Testing Recommendations

1. **Pagination Logic**
   - Test boundary conditions (page 1, last page)
   - Test page size changes
   - Verify correct items are displayed

2. **Integration**
   - Test with search filters on patient detail page
   - Test with sorting controls
   - Test with different data volumes

3. **UI/UX**
   - Verify responsive layout on mobile
   - Test keyboard navigation
   - Check alignment with design system

## Future Enhancements

1. **URL Query Parameters**: Store pagination state in URL (?page=2&size=25)
2. **Server-Side Pagination**: Implement with backend API for large datasets
3. **Lazy Loading**: Add infinite scroll option
4. **Jump to Page**: Text input for direct page navigation
5. **Analytics**: Track pagination usage patterns

## Files Modified

### New Files
- `/frontend/components/ui/pagination.tsx` - Pagination component
- `/frontend/hooks/usePagination.ts` - Pagination logic hook

### Modified Files
- `/frontend/app/therapist/page.tsx` - Added pagination to patient list
- `/frontend/app/therapist/patients/[id]/page.tsx` - Added pagination to session list

## Dependencies
- React 19 (already in project)
- Lucide React (already in project for icons)
- Tailwind CSS (already in project)
- Existing UI components (Button, Select)

## Notes for Future Developers

1. Both pagination instances use different page size options to match their respective layouts
2. The hook is generic and reusable for any list-based component
3. Pagination only shows when necessary (items > pageSize)
4. State is client-side only; consider server-side pagination for datasets > 1000 items
5. The Select component from the UI library handles the page size dropdown
