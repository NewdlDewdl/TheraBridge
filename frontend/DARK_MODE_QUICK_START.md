# Dark Mode - Quick Start Guide

## What Was Done

Dark mode support has been fully implemented using `next-themes` and Tailwind CSS. Everything is ready to use!

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```

### 3. Test Dark Mode
- Open `http://localhost:3000/therapist` or `/patient`
- Look for the sun/moon icon in the top-right corner
- Click to toggle between light and dark modes
- Reload the page - your choice is saved!

## What Works

✅ **Theme Toggle Button**
- Click the sun/moon icon in the header
- Instantly switches between light and dark modes

✅ **Automatic System Detection**
- App respects your OS dark mode setting on first visit
- You can override it with the toggle

✅ **Persistent Storage**
- Your theme choice is saved automatically
- Persists across browser sessions

✅ **All Components Support Dark Mode**
- Buttons, cards, forms, inputs - all automatically themed
- Toast notifications match the current theme

## Using Dark Mode in Your Code

### If You Just Want to Check the Current Theme
```tsx
'use client';

import { useTheme } from 'next-themes';

export function MyComponent() {
  const { theme } = useTheme();
  return <div>Current: {theme}</div>;
}
```

### To Add the Toggle Button Somewhere
```tsx
import { ThemeToggle } from '@/components/ui/theme-toggle';

export function Header() {
  return (
    <header>
      <h1>My App</h1>
      <ThemeToggle />
    </header>
  );
}
```

### To Add Custom Dark Mode Styling to a Component
```tsx
<div className="bg-white dark:bg-black text-black dark:text-white">
  This automatically adapts to dark mode!
</div>
```

## File Locations

**New Components:**
- `components/providers/theme-provider.tsx` - Main theme provider
- `components/ui/theme-toggle.tsx` - Toggle button

**Updated Files:**
- `app/layout.tsx` - Added theme provider
- `app/globals.css` - Added dark mode colors
- `app/therapist/layout.tsx` - Added theme toggle
- `app/patient/layout.tsx` - Added theme toggle
- `components/providers/toaster-provider.tsx` - Theme-aware toasts

## Common Questions

**Q: Where is the theme toggle button?**
A: Top-right corner of the header on `/therapist` and `/patient` pages

**Q: How do I test dark mode?**
A: Click the theme toggle button to switch instantly

**Q: Does dark mode persist?**
A: Yes! Your choice is saved in browser storage

**Q: Does it respect system preferences?**
A: Yes! On first visit, it checks your OS dark mode setting

**Q: Can I add dark mode to my own components?**
A: Yes! Use `dark:` utilities in className, or use `useTheme()` hook

## Troubleshooting

**Theme toggle doesn't appear?**
- Make sure you're on `/therapist` or `/patient` pages
- Check browser console for errors
- Try reloading the page

**Dark mode not working?**
- Clear browser cache/reload (Cmd+Shift+R or Ctrl+Shift+R)
- Check if next-themes is installed: `npm list next-themes`
- Check browser console for errors

**Theme doesn't persist?**
- Make sure browser's LocalStorage is enabled
- Check in DevTools: Application → LocalStorage → therapybridge-theme

## Next Steps

1. Test the dark mode thoroughly
2. Make sure all your custom components look good in both themes
3. If you need help, see `DARK_MODE_GUIDE.md` for detailed documentation
4. For implementation details, see `DARK_MODE_IMPLEMENTATION_SUMMARY.md`

## Key Points to Remember

- Next-themes library handles all the complexity
- CSS variables in `globals.css` control the theme colors
- Tailwind's `dark:` utilities work automatically
- All components automatically support dark mode
- Theme toggle button is in the header on both dashboards
- User preferences are saved automatically

---

**Everything is set up and ready to use!** Just run the dev server and test it out.
