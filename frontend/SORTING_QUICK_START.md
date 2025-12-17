# Sorting Controls - Quick Start Guide

## What Was Added

Sorting controls have been added to two main areas:

1. **Therapist Dashboard** (`/therapist`) - Sort patient cards
2. **Patient Detail Page** (`/therapist/patients/[id]`) - Sort sessions

## User Features

### On Therapist Dashboard

**Sort Patients By:**
- Patient Name (A-Z or Z-A)
- Latest Session Date (Newest or Oldest first)
- Total Sessions (Most or Least)

**UI Location:** Top-right corner above patient cards

**How to Use:**
1. Click the "Sort:" dropdown to change sort field
2. Click the arrow button to toggle sort direction
3. The label updates to show current order (e.g., "A-Z", "Newest First")

### On Patient Detail Page

**Sort Sessions By:**
- Date (Newest or Oldest first)
- Patient Name (A-Z or Z-A)
- Status (A-Z or Z-A)

**UI Location:** Next to the search input

**How to Use:**
1. Click the "Sort:" dropdown to change sort field
2. Click the arrow button to toggle sort direction
3. The label updates to show current order
4. Works seamlessly with search and existing filters

## Visual Indicators

**Arrow Icons:**
- ↑ (Up arrow) = Ascending order
- ↓ (Down arrow) = Descending order

**Dynamic Labels:**
- Date sorting: "Newest First" / "Oldest First"
- Text sorting: "A-Z" / "Z-A"
- Number sorting: "Most" / "Least"

## Default Behavior

**Patient Dashboard:**
- Default sort: Patient Name, A-Z

**Patient Detail Page:**
- Default sort: Session Date, Newest First

## Files to Review

For developers:

1. **Hooks:**
   - `/hooks/useSessionSort.ts` - Session sorting logic
   - `/hooks/usePatientSort.ts` - Patient sorting logic

2. **Components:**
   - `/components/SessionSortControl.tsx` - Session sort UI
   - `/components/PatientSortControl.tsx` - Patient sort UI

3. **Pages:**
   - `/app/therapist/page.tsx` - Therapist dashboard
   - `/app/therapist/patients/[id]/page.tsx` - Patient detail

## Integration with Existing Features

- **Search**: Sorting applies AFTER search filters results
- **Status Filters**: Sorting applies AFTER status/date filters
- **Responsive Design**: Controls adapt to mobile/tablet/desktop

## Future Enhancements

Possible improvements:
- Save sort preferences to user account
- Multiple-level sorting
- Custom sort combinations
- Export sorted data

## Troubleshooting

**Sort not working?**
- Ensure you have data (patients or sessions)
- Check browser console for errors
- Try refreshing the page

**Unexpected sort order?**
- Note: String sorting is case-insensitive (A-Z includes lowercase)
- Date sorting uses the session_date field
- Patient name sorting requires patient data to be loaded

## Browser Support

Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- No special plugins required
- Responsive on mobile and desktop
- Uses standard JavaScript Array.sort()
