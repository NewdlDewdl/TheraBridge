# Dark Mode Implementation Guide

## Overview

Dark mode support has been fully implemented using `next-themes` with Tailwind CSS. The implementation includes:
- Automatic dark mode detection based on system preferences
- LocalStorage persistence of user theme choice
- No flash of unstyled content (FOUC)
- Theme toggle button in both Therapist and Patient dashboards
- Dynamic theme awareness for Sonner toast notifications

## Installation & Setup

### 1. Package Installation
```bash
npm install next-themes
```

**Version**: `^0.4.6` (already added to package.json)

### 2. Root Layout Configuration

The root layout (`app/layout.tsx`) has been updated with:

```tsx
import { ThemeProvider } from "@/components/providers/theme-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>
            <ToasterProvider />
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**Key points:**
- `suppressHydrationWarning` prevents hydration mismatch warnings when switching themes
- `ThemeProvider` wraps everything to provide theme context globally
- Placed above `AuthProvider` and `ToasterProvider` to apply to all children

### 3. Files Created/Modified

#### New Files Created:
1. **`components/providers/theme-provider.tsx`**
   - Wraps next-themes' ThemeProvider
   - Configuration: class-based dark mode detection
   - Storage key: `therapybridge-theme`
   - Default theme: system preference

2. **`components/ui/theme-toggle.tsx`**
   - Reusable theme toggle button component
   - Shows sun icon in light mode, moon icon in dark mode
   - Handles hydration mismatch with mounted state
   - Accessible with proper aria labels

#### Modified Files:
1. **`app/layout.tsx`**
   - Added ThemeProvider import and wrapper
   - Added `suppressHydrationWarning` to html element

2. **`app/globals.css`**
   - Added dark mode color variables in `.dark` class
   - All existing CSS variables have dark counterparts
   - Uses HSL color space for easy theming

3. **`app/therapist/layout.tsx`**
   - Added ThemeToggle component to header
   - Positioned on the right side of the header

4. **`app/patient/layout.tsx`**
   - Added ThemeToggle component to header
   - Positioned on the right side of the header

5. **`components/providers/toaster-provider.tsx`**
   - Updated to dynamically switch theme based on current theme
   - Syncs Sonner toast notifications with app theme
   - Prevents hydration mismatch with mounted state check

## Color Scheme

### Light Mode Variables (Default)
```css
--background: 0 0% 100%;        /* White */
--foreground: 222.2 84% 4.9%;   /* Dark blue */
--primary: 221.2 83.2% 53.3%;   /* Blue */
--destructive: 0 84.2% 60.2%;   /* Red */
/* ... and more */
```

### Dark Mode Variables
```css
--background: 222.2 84% 4.9%;   /* Dark blue */
--foreground: 210 40% 98%;      /* Near white */
--primary: 217.2 91.2% 59.8%;   /* Lighter blue */
--destructive: 0 72.2% 50.6%;   /* Brighter red */
/* ... and more */
```

All colors use HSL format for consistency with existing Tailwind setup.

## Usage

### Using the Theme Hook

In any client component, use the `useTheme` hook from next-themes:

```tsx
'use client';

import { useTheme } from 'next-themes';

export function MyComponent() {
  const { theme, setTheme, themes } = useTheme();

  return (
    <div>
      <p>Current theme: {theme}</p>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('light')}>Light</button>
      <button onClick={() => setTheme('system')}>System</button>
    </div>
  );
}
```

### Using the Theme Toggle Component

```tsx
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function Header() {
  return (
    <header className="flex justify-between items-center">
      <h1>My App</h1>
      <ThemeToggle />
    </header>
  );
}
```

## Adding Dark Mode Support to Components

### Using Tailwind's `dark:` Prefix

For components that need custom styling in dark mode, use Tailwind's dark mode utilities:

```tsx
<div className="bg-white dark:bg-slate-900 text-black dark:text-white">
  Content that adapts to theme
</div>
```

### Using CSS Variables (Recommended)

Since the project already uses CSS custom properties, most components work automatically:

```tsx
<div className="bg-background text-foreground">
  Already adapts to theme via CSS variables
</div>
```

All existing components using color variables (primary, secondary, accent, etc.) automatically support dark mode.

## Common Patterns

### Safe Client Component Pattern

To avoid hydration mismatches, follow this pattern when using `useTheme()`:

```tsx
'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export function ThemeAwareComponent() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div>Loading...</div>; // Render placeholder until mounted
  }

  return (
    <div className={theme === 'dark' ? 'dark-styles' : 'light-styles'}>
      Theme: {theme}
    </div>
  );
}
```

### Form Components

All form components (Button, Input, Select, etc.) use CSS variables and support dark mode automatically.

Example with explicit dark mode support:

```tsx
<input
  className="
    bg-background text-foreground
    border border-input
    dark:bg-slate-900 dark:border-slate-700
  "
/>
```

## Theme Storage

- **Storage Key**: `therapybridge-theme`
- **Storage Type**: LocalStorage
- **Persisted Values**: `light`, `dark`, or `system`
- **Default**: System preference (respects OS settings)

Users' theme preference is automatically saved and restored on page reload.

## Testing

### Manual Testing Checklist

1. **Light Mode**
   - Visit `/therapist` or `/patient`
   - Verify all components render correctly
   - Click theme toggle, toggle should show moon icon

2. **Dark Mode**
   - Click theme toggle
   - Verify dark backgrounds and light text
   - Check all form elements are visible
   - Verify primary buttons are still visible
   - Toggle should show sun icon

3. **Persistence**
   - Set theme to dark
   - Reload page
   - Verify theme remains dark

4. **System Preference**
   - Clear localStorage: `localStorage.removeItem('therapybridge-theme')`
   - Change OS theme setting
   - Reload page
   - Verify app follows OS theme

5. **Toast Notifications**
   - In dark mode, trigger a toast notification
   - Verify toast has dark background
   - In light mode, verify toast has light background

## Troubleshooting

### Flash of Unstyled Content (FOUC)

If you see a flash of light mode before switching to dark:
- Ensure `suppressHydrationWarning` is on the `<html>` element
- Ensure `ThemeProvider` is early in the component tree

### Hydration Mismatch Warnings

If you see hydration warnings:
- Use the mounted state pattern for components that read theme
- Ensure all theme-reading components are marked with `'use client'`

### Theme Not Persisting

- Check browser's LocalStorage is enabled
- Verify the storage key is `therapybridge-theme`
- Check browser console for errors

### Specific Component Styling Issues

For components that need special dark mode styling:

```tsx
// Add dark: utilities alongside regular utilities
<div className="bg-white text-black dark:bg-slate-900 dark:text-white">
  Custom dark mode styling
</div>
```

## Best Practices

1. **Use CSS Variables When Possible**
   - Defined in `globals.css` for consistency
   - Automatically adapt to theme
   - Less code duplication

2. **Handle Hydration Correctly**
   - Use `useEffect` with mounted state for theme-dependent rendering
   - Place mounted check in components using `useTheme()`
   - Prevents hydration mismatch warnings

3. **Test Both Themes**
   - Always test components in both light and dark modes
   - Pay attention to contrast and readability
   - Test with different OS theme settings

4. **Keep Color Scheme Consistent**
   - Add new theme-aware colors to `globals.css`
   - Maintain similar contrast ratios in both modes
   - Use the same HSL format for all colors

## Adding More Color Customization

To add new theme colors:

1. Add CSS variables to `:root` and `.dark` in `globals.css`:
```css
:root {
  --custom-color: 200 50% 50%;
}

.dark {
  --custom-color: 200 50% 60%;
}
```

2. Update Tailwind config if using the color:
```ts
// tailwind.config.ts
colors: {
  customColor: "hsl(var(--custom-color))",
}
```

3. Use in components:
```tsx
<div className="bg-customColor">Custom themed element</div>
```

## Dependencies

- **next-themes**: ^0.4.6
- **next**: 16.0.10
- **tailwindcss**: ^3.4.0 (with `darkMode: ["class"]`)
- **React**: 19.2.1

## References

- [next-themes Documentation](https://github.com/pacocoursey/next-themes)
- [Tailwind CSS Dark Mode](https://tailwindcss.com/docs/dark-mode)
- [Web Content Accessibility Guidelines - Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
