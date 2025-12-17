# Pagination Usage Examples

## Quick Start

### Using Pagination in Your Component

#### 1. Import the hook and component
```typescript
import { usePagination } from '@/hooks/usePagination';
import { Pagination } from '@/components/ui/pagination';
```

#### 2. Add pagination to your data
```typescript
function MyListComponent() {
  const [data, setData] = useState<Item[]>([]); // Your data

  // Use the pagination hook
  const {
    currentPage,
    pageSize,
    totalPages,
    paginatedItems,
    onPageChange,
    onPageSizeChange,
  } = usePagination(data, { initialPageSize: 10 });

  return (
    <>
      {/* Display paginated items */}
      <div className="grid gap-4">
        {paginatedItems.map(item => (
          <ItemCard key={item.id} item={item} />
        ))}
      </div>

      {/* Show pagination controls */}
      {data.length > pageSize && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={data.length}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
          pageSizeOptions={[10, 25, 50]}
        />
      )}
    </>
  );
}
```

## Real-World Examples

### Example 1: Patient List (from therapist/page.tsx)
```typescript
// State
const { patients } = usePatients();
const { sortedPatients } = usePatientSort(patients, patientStats);

// Pagination
const {
  currentPage,
  pageSize,
  totalPages,
  paginatedItems: paginatedPatients,
  onPageChange,
  onPageSizeChange,
} = usePagination(sortedPatients || [], { initialPageSize: 9 });

// Render
<div className="space-y-6">
  {/* Grid of items */}
  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
    {paginatedPatients.map(patient => (
      <PatientCard key={patient.id} patient={patient} />
    ))}
  </div>

  {/* Pagination controls */}
  {(sortedPatients?.length || 0) > pageSize && (
    <div className="flex justify-center pt-4">
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={sortedPatients?.length || 0}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        pageSizeOptions={[9, 18, 27, 36]}
      />
    </div>
  )}
</div>
```

### Example 2: Session List with Filters (from patients/[id]/page.tsx)
```typescript
// State
const { sessions } = useSessions({ patientId: id });
const { filteredSessions, ... } = useSessionSearch(sessions, ...);
const { sortedSessions } = useSessionSort(...);

// Display sessions after applying filters
const displaySessions = hasActiveSearch ? filteredSessions : sortedSessions;

// Pagination applies to filtered/sorted results
const {
  currentPage,
  pageSize,
  totalPages,
  paginatedItems: paginatedSessions,
  onPageChange,
  onPageSizeChange,
} = usePagination(displaySessions, { initialPageSize: 10 });

// Render with optional pagination
<div className="space-y-6">
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {paginatedSessions.map(session => (
      <SessionCard key={session.id} session={session} />
    ))}
  </div>

  {displaySessions.length > pageSize && (
    <div className="flex justify-center pt-4">
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={displaySessions.length}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        pageSizeOptions={[10, 25, 50, 100]}
      />
    </div>
  )}
</div>
```

## Configuration Options

### usePagination Hook Options
```typescript
interface UsePaginationOptions {
  initialPageSize?: number;      // Default: 10
  pageSizeOptions?: number[];    // Default: [10, 25, 50, 100]
}

// Usage
const pagination = usePagination(items, {
  initialPageSize: 25,
  pageSizeOptions: [5, 10, 25, 50, 100]
});
```

### Pagination Component Props
```typescript
interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  pageSizeOptions?: number[];    // Optional: override default options
  className?: string;            // Optional: add custom CSS classes
}
```

## Advanced Patterns

### 1. Pagination with Server-Side Data Filtering
```typescript
const MyComponent = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  
  // Fetch data based on pagination params
  const { data } = useFetchData({
    page,
    pageSize,
    // Send to backend
  });

  return (
    <>
      {/* Display data */}
      <ItemList items={data.items} />
      
      {/* Use pagination to control fetch params */}
      <Pagination
        currentPage={page}
        pageSize={pageSize}
        totalPages={data.totalPages}
        totalItems={data.totalCount}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </>
  );
};
```

### 2. Pagination with Search Results
```typescript
const SearchResults = ({ searchTerm }) => {
  const [allResults] = useSearch(searchTerm);
  
  // Paginate search results
  const {
    paginatedItems: results,
    currentPage,
    totalPages,
    pageSize,
    onPageChange,
    onPageSizeChange,
  } = usePagination(allResults);

  return (
    <>
      <ResultsList items={results} />
      {allResults.length > pageSize && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={allResults.length}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
        />
      )}
    </>
  );
};
```

### 3. Conditional Pagination Display
```typescript
// Only show pagination if there are items
{items.length > pageSize && (
  <Pagination {...props} />
)}

// Or with custom message
{items.length > pageSize ? (
  <Pagination {...props} />
) : (
  <p className="text-center text-muted-foreground">
    All {items.length} items shown
  </p>
)}
```

## Customization

### Custom Page Size Options
```typescript
// For products listing
<Pagination
  {...commonProps}
  pageSizeOptions={[12, 24, 48]}  // 3x4, 4x6, 6x8 grids
/>

// For data tables
<Pagination
  {...commonProps}
  pageSizeOptions={[5, 10, 25, 100]}  // Database standard
/>
```

### Custom Styling
```typescript
<Pagination
  {...commonProps}
  className="mt-8 border-t pt-8"  // Add custom margins/borders
/>
```

## Testing Examples

### Test Pagination Logic
```typescript
import { renderHook, act } from '@testing-library/react';
import { usePagination } from '@/hooks/usePagination';

describe('usePagination', () => {
  it('should paginate items correctly', () => {
    const items = Array.from({ length: 25 }, (_, i) => i);
    const { result } = renderHook(() => 
      usePagination(items, { initialPageSize: 10 })
    );

    expect(result.current.paginatedItems).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    expect(result.current.totalPages).toBe(3);

    act(() => result.current.onPageChange(2));
    expect(result.current.paginatedItems).toEqual([10, 11, 12, 13, 14, 15, 16, 17, 18, 19]);
  });
});
```

## Performance Tips

1. **Only render pagination when needed**
   ```typescript
   {data.length > pageSize && <Pagination {...props} />}
   ```

2. **Memoize large lists**
   ```typescript
   const memoizedItems = useMemo(() => data, [data]);
   const pagination = usePagination(memoizedItems);
   ```

3. **Consider server-side pagination for large datasets**
   - Use pagination component with backend API calls
   - Reduces memory usage for datasets > 10,000 items

## Common Issues & Solutions

### Issue: Pagination doesn't appear
**Solution:** Check that `items.length > pageSize`. Pagination only shows when necessary.

### Issue: Items reset to page 1 unexpectedly
**Solution:** This happens when page size changes. It's intentional to prevent invalid page numbers.

### Issue: Page size selector shows wrong options
**Solution:** Pass `pageSizeOptions` prop to Pagination component.

### Issue: Pagination doesn't work with filtered data
**Solution:** Pass filtered array to hook: `usePagination(filteredItems)`

## Accessibility

The pagination component includes:
- Screen reader text for icon buttons
- Proper disabled states
- Semantic HTML buttons
- Keyboard accessible via Tab navigation
- ARIA labels for context

No additional accessibility setup needed!
