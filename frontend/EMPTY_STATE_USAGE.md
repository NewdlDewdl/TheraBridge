# EmptyState Component Usage Guide

The `EmptyState` component provides a consistent, reusable way to display empty states across the application. It includes an icon, heading, description, and optional action button.

## Component Location

```
components/EmptyState.tsx
```

## Basic Usage

```tsx
import { EmptyState } from '@/components/EmptyState';
import { Users } from 'lucide-react';

export function MyComponent() {
  const items = [];

  if (items.length === 0) {
    return (
      <EmptyState
        icon={Users}
        heading="No users found"
        description="Create your first user to get started"
        actionLabel="Add User"
        onAction={() => handleAddUser()}
      />
    );
  }

  return <div>{/* render items */}</div>;
}
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `icon` | `LucideIcon` | Yes | - | Icon component from lucide-react |
| `heading` | `string` | Yes | - | Main heading text |
| `description` | `string` | Yes | - | Description text |
| `actionLabel` | `string` | No | - | Action button label |
| `onAction` | `() => void` | No | - | Action button click handler |
| `actionVariant` | `string` | No | `'default'` | Button variant: `default`, `outline`, `secondary`, `ghost`, `link`, `destructive` |
| `className` | `string` | No | - | Custom className for container |
| `iconClassName` | `string` | No | - | Custom className for icon |
| `showCard` | `boolean` | No | `true` | Wrap in Card component or show as standalone |
| `iconSize` | `'sm' \| 'md' \| 'lg'` | No | `'lg'` | Icon size: `sm` (8x8), `md` (12x12), `lg` (16x16) |

## Examples

### With Action Button

```tsx
<EmptyState
  icon={Plus}
  heading="No patients yet"
  description="Add your first patient to get started"
  actionLabel="Add Patient"
  onAction={() => openPatientModal()}
/>
```

### Without Card Wrapper

```tsx
<EmptyState
  icon={Users}
  heading="No results"
  description="Try adjusting your search filters"
  showCard={false}
/>
```

### With Custom Styling

```tsx
<EmptyState
  icon={Calendar}
  heading="No sessions"
  description="Upload your first session"
  iconSize="md"
  iconClassName="text-blue-500"
  actionVariant="outline"
  actionLabel="Upload"
  onAction={() => openUploader()}
/>
```

### Search Results Empty State

```tsx
{filteredItems.length === 0 ? (
  <EmptyState
    icon={Search}
    heading="No results found"
    description={`No items match "${searchQuery}"`}
    showCard
  />
) : (
  <ItemList items={filteredItems} />
)}
```

## Currently Integrated Locations

### ✓ Therapist Dashboard (`app/therapist/page.tsx`)
- Empty state when no patients exist
- Uses `Users` icon with "Add Patient" action

### ✓ Patient Detail Page (`app/therapist/patients/[id]/page.tsx`)
- Empty state when no sessions uploaded
- Empty state when search produces no results
- Uses `Calendar` icon

### ✓ Patient Portal (`app/patient/page.tsx`)
- Empty state for no active strategies
- Empty state for no action items
- Empty state for no sessions
- Uses `Target`, `CheckCircle`, and `MessageCircle` icons

## Icon Options

The component accepts any icon from [lucide-react](https://lucide.dev/). Common icons for empty states:

- `Users` - For user/patient lists
- `Calendar` - For sessions/events
- `Target` - For strategies/goals
- `CheckCircle` - For action items
- `MessageCircle` - For conversations/feedback
- `Inbox` - For notifications
- `Search` - For search results
- `ShoppingCart` - For carts/collections
- `FileText` - For documents
- `Settings` - For configuration

## Styling

The component uses Tailwind CSS classes and integrates with the existing design system:
- Text colors use semantic classes (`text-muted-foreground`, etc.)
- Padding and spacing follow card conventions
- Icons are centered and size-responsive
- Content is centered with max-width constraint

## Responsive Behavior

- Icons scale based on `iconSize` prop
- Text wraps naturally on smaller screens
- Button adapts to available space
- Card wrapper remains responsive

## Best Practices

1. **Always provide clear messaging**: The heading should answer "Why is this empty?" and description should suggest next steps.

2. **Use appropriate icons**: Choose icons that visually represent the data type (calendar for sessions, users for people, etc.).

3. **Include action when possible**: Provide a button when users can take immediate action to fill the empty state.

4. **Search empty states**: Show different messaging when results are empty due to search filters vs. truly no data.

5. **Loading states**: Use loading skeletons before showing empty states to avoid flickering.

6. **Consistent sizing**: Use `iconSize="md"` for most cases, `"sm"` for dense layouts, `"lg"` for featured sections.

## Example: Conditional Empty States

```tsx
{isLoading ? (
  <LoadingSkeleton />
) : items.length === 0 ? (
  <EmptyState
    icon={Package}
    heading="No items available"
    description="Start by creating your first item"
    actionLabel="Create Item"
    onAction={handleCreate}
  />
) : (
  <ItemGrid items={items} />
)}
```

## Example: Search with Empty State

```tsx
{filteredItems.length === 0 ? (
  <EmptyState
    icon={Search}
    heading={hasSearchQuery ? "No results" : "No items"}
    description={
      hasSearchQuery
        ? `No items match "${searchQuery}"`
        : "Start by creating your first item"
    }
    actionLabel={!hasSearchQuery ? "Create" : undefined}
    onAction={!hasSearchQuery ? handleCreate : undefined}
  />
) : (
  <ItemList items={filteredItems} />
)}
```
