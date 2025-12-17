# EmptyState Component - Visual Examples

## Example 1: Therapist Dashboard - No Patients

### Props
```typescript
<EmptyState
  icon={Users}
  heading="No patients yet"
  description="Add your first patient to get started"
  actionLabel="Add Patient"
  onAction={() => openPatientCreationModal()}
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│              👥                      │
│                                     │
│        No patients yet              │
│    Add your first patient to        │
│        get started                  │
│                                     │
│         [ + Add Patient ]           │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- New therapist with no patients assigned
- First-time user onboarding
- After deleting all patients (recovery flow)

---

## Example 2: Patient Detail Page - No Sessions

### Props
```typescript
<EmptyState
  icon={Calendar}
  heading="No sessions yet"
  description="Upload your first session to get started"
  iconSize="md"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│             📅                      │
│                                     │
│      No sessions yet                │
│  Upload your first session to       │
│     get started                     │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- Newly added patient with no session history
- Context: Below upload form to show next step
- Encourages user to upload first session

---

## Example 3: Session Search - No Results

### Props
```typescript
<EmptyState
  icon={Calendar}
  heading="No sessions found"
  description={`No sessions match "${searchQuery}"`}
  iconSize="md"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│             📅                      │
│                                     │
│    No sessions found                │
│  No sessions match "anxiety"        │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- User performed a search that yielded no results
- Different from "no sessions" (which is about data, not search)
- Suggests trying different search terms

---

## Example 4: Patient Portal - No Active Strategies

### Props
```typescript
<EmptyState
  icon={Target}
  heading="No active strategies yet"
  description="Work with your therapist to identify strategies for your treatment plan"
  iconSize="md"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│             🎯                      │
│                                     │
│  No active strategies yet           │
│  Work with your therapist to        │
│ identify strategies for your        │
│     treatment plan                  │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- Patient has no therapeutic strategies assigned yet
- Educates patient about next steps
- No action button (patient cannot self-create)

---

## Example 5: Patient Portal - No Action Items

### Props
```typescript
<EmptyState
  icon={CheckCircle}
  heading="No action items yet"
  description="Your therapist will share action items after your sessions"
  iconSize="md"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│             ✓                       │
│                                     │
│    No action items yet              │
│ Your therapist will share action    │
│  items after your sessions          │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- Patient has completed sessions but none assigned action items
- Sets clear expectation that therapist will provide them
- Reassuring messaging

---

## Example 6: Patient Portal - No Sessions

### Props
```typescript
<EmptyState
  icon={MessageCircle}
  heading="No sessions yet"
  description="Schedule your first session with your therapist to get started"
  iconSize="md"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│                                     │
│             💬                      │
│                                     │
│      No sessions yet                │
│  Schedule your first session with   │
│  your therapist to get started      │
│                                     │
└─────────────────────────────────────┘
```

### Use Case
- New patient with no session history
- Encourages scheduling first appointment
- Clear next action

---

## Example 7: Custom Icon and Variant

### Props
```typescript
<EmptyState
  icon={AlertCircle}
  heading="No results"
  description="Try adjusting your filters"
  actionLabel="Clear Filters"
  actionVariant="outline"
  onAction={() => clearAllFilters()}
  iconSize="sm"
  showCard
/>
```

### Visual Output
```
┌─────────────────────────────────────┐
│    ⚠️      No results               │
│  Try adjusting your filters         │
│   [ Clear Filters ]                 │
└─────────────────────────────────────┘
```

### Use Case
- Filter/search produced no results
- Outline button variant for secondary action
- Smaller icon for compact layouts
- Helps user recover from empty result state

---

## Icon Size Variations

### Small (sm) - 8x8
```
┌──────────────┐
│   🎯         │
│ Compact      │
│ Layout       │
└──────────────┘
```

### Medium (md) - 12x12
```
┌──────────────┐
│     🎯       │
│ Balanced     │
│ Default      │
└──────────────┘
```

### Large (lg) - 16x16
```
┌──────────────┐
│      🎯      │
│ Featured     │
│ Section      │
└──────────────┘
```

---

## Button Variant Examples

### Default
```
[ + Add Patient ]  (blue/primary)
```

### Outline
```
[ Clear Filters ]  (gray outline)
```

### Secondary
```
[ Try Again ]  (secondary color)
```

### Ghost
```
[ Learn More ]  (subtle/minimal)
```

### Link
```
Learn More  (underlined text)
```

### Destructive
```
[ Delete All ]  (red warning)
```

---

## Responsive Behavior

### Desktop (Wide)
```
┌─────────────────────────────────────┐
│                                     │
│              🎯                      │
│                                     │
│    No active strategies yet         │
│ Work with your therapist to         │
│ identify strategies for your        │
│     treatment plan                  │
│                                     │
└─────────────────────────────────────┘
```

### Tablet (Medium)
```
┌────────────────────────┐
│                        │
│          🎯            │
│                        │
│   No active           │
│   strategies yet       │
│ Work with your        │
│ therapist to          │
│ identify strategies   │
│                        │
└────────────────────────┘
```

### Mobile (Narrow)
```
┌──────────────┐
│              │
│      🎯      │
│              │
│ No active    │
│ strategies   │
│ yet          │
│              │
│ Work with    │
│ your         │
│ therapist    │
│ to identify  │
│ strategies   │
│              │
└──────────────┘
```

---

## Common Icon Usage Patterns

| Scenario | Icon | Heading | Description |
|----------|------|---------|-------------|
| No data items | Package, Inbox, FileText | "No {items}" | "Create your first {item}" |
| No people | Users, User | "No {people}" | "Add your first {person}" |
| No events | Calendar, Clock | "No {events}" | "Schedule your first {event}" |
| No messages | MessageCircle, Mail | "No {messages}" | "Send your first {message}" |
| No results | Search, Zap | "No results" | "Try adjusting filters" |
| No settings | Settings, Sliders | "Not configured" | "Set up your {feature}" |

---

## Implementation Checklist

When adding a new empty state, use this checklist:

- [ ] Choose appropriate icon from lucide-react
- [ ] Write clear, action-oriented heading
- [ ] Write helpful description text
- [ ] Determine if action button is needed
- [ ] Choose appropriate button variant
- [ ] Decide on icon size (sm, md, lg)
- [ ] Set showCard to true or false
- [ ] Test on mobile, tablet, desktop
- [ ] Verify text is visible and readable
- [ ] Check accessibility with screen reader
- [ ] Ensure button action is implemented (TODO if not)

---

## Internationalization (i18n) Ready

All text can be easily translated:

```typescript
<EmptyState
  icon={Users}
  heading={t('therapist.dashboard.noPatients')}
  description={t('therapist.dashboard.addFirstPatient')}
  actionLabel={t('common.addPatient')}
  onAction={openPatientModal}
/>
```

### Translation Keys Pattern
```
therapist.dashboard.noPatients
therapist.dashboard.addFirstPatient
patient.portal.noSessions
patient.portal.noStrategies
common.addPatient
common.tryAgain
```

---

## Animation Possibilities (Future Enhancement)

```typescript
// Potential fade-in animation on mount
<EmptyState
  icon={Calendar}
  heading="No sessions"
  description="Get started..."
  className="animate-fade-in"
/>

// Potential icon animation
<EmptyState
  icon={Users}
  heading="No patients"
  description="..."
  iconClassName="animate-bounce"
/>
```
