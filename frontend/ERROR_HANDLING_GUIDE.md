# Error Handling Guide

This guide explains how to use the improved error handling system in the TherapyBridge frontend.

## Overview

The error handling system consists of:

1. **ErrorMessage Component** - Reusable UI component for displaying errors with different variants
2. **Error Formatter** - Utility functions that convert API errors to user-friendly messages
3. **Error Context** - Global error management using React Context
4. **Error Types** - Strongly-typed error handling with TypeScript

## Components

### ErrorMessage Component

The `ErrorMessage` component is a flexible, reusable component for displaying errors with different visual styles.

**Location:** `/components/ui/error-message.tsx`

**Variants:**
- `inline` - Compact inline error (left-bordered)
- `alert` - Full-width alert box
- `toast` - Toast notification style
- `banner` - Page-level banner alert

**Severity Levels:**
- `error` - Red styling for critical errors
- `warning` - Amber styling for warnings
- `info` - Blue styling for informational messages

**Features:**
- Auto-dismiss on timeout
- Dismissible with close button
- Optional action button with callback
- Field-level error display

**Basic Usage:**

```tsx
import { ErrorMessage } from '@/components/ui/error-message';

function MyComponent() {
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      {error && (
        <ErrorMessage
          message={error}
          variant="alert"
          severity="error"
          dismissible
          onDismiss={() => setError(null)}
        />
      )}
    </>
  );
}
```

**Convenience Components:**

For quick usage, import pre-configured variants:

```tsx
import {
  ErrorMessageInline,
  ErrorMessageAlert,
  ErrorMessageToast,
  ErrorMessageBanner,
} from '@/components/ui/error-message';

// These are equivalent to ErrorMessage with variant pre-set
<ErrorMessageAlert message="An error occurred" />
<ErrorMessageToast message="Upload failed" />
<ErrorMessageInline message="Email is required" />
<ErrorMessageBanner message="System maintenance" />
```

## Error Formatter

The error formatter converts API errors to user-friendly messages with suggestions.

**Location:** `/lib/error-formatter.ts`

**Main Functions:**

### `formatApiError(error: FailureResult | ApiErrorType): FormattedError`

Converts any API error to a user-friendly format:

```tsx
import { formatApiError } from '@/lib/error-formatter';

try {
  const result = await apiClient.get('/patients/123');
  if (!result.success) {
    const error = formatApiError(result);
    console.log(error.message);      // "Patient not found"
    console.log(error.suggestion);   // "Check the patient ID and try again"
    console.log(error.retryable);    // true/false
  }
} catch (err) {
  const formatted = formatApiError(err);
}
```

**Returned Error Object:**

```typescript
interface FormattedError {
  message: string;           // Main error message
  description?: string;      // Additional details
  suggestion?: string;       // What to do about it
  severity: 'error' | 'warning' | 'info';
  retryable: boolean;        // Can the user retry?
  fieldErrors?: Record<string, string>; // Field-specific errors
}
```

### Context-Specific Formatters

Use these formatters for specific contexts:

```tsx
import {
  formatUploadError,
  formatAuthError,
  formatDataFetchError,
} from '@/lib/error-formatter';

// For file uploads
try {
  await uploadFile(file);
} catch (err) {
  const error = formatUploadError(err);
  // Returns: "File too large", "Upload timed out", etc.
}

// For authentication
try {
  await login(email, password);
} catch (err) {
  const error = formatAuthError(err);
  // Returns: "Invalid credentials", "Email already registered", etc.
}

// For data fetching
try {
  const data = await fetchData();
} catch (err) {
  const error = formatDataFetchError(err);
  // Returns: "Failed to load data", "Resource not found", etc.
}
```

### HTTP Status Code Handling

The formatter automatically handles different HTTP status codes:

- **400** - Bad Request → "Invalid request"
- **401** - Unauthorized → "Session expired"
- **403** - Forbidden → "Access denied"
- **404** - Not Found → "Resource not found"
- **409** - Conflict → "Resource conflict"
- **422** - Validation Error → "Validation failed" with field errors
- **429** - Too Many Requests → "Too many requests"
- **500** - Server Error → "Server error"
- **503** - Service Unavailable → "Service unavailable"

## Error Context

Use the error context for global error management across your app.

**Location:** `/lib/error-context.tsx`

### Setup

Wrap your app with the error provider:

```tsx
import { ErrorProvider } from '@/lib/error-context';

export default function App() {
  return (
    <ErrorProvider>
      <YourApp />
    </ErrorProvider>
  );
}
```

### useErrorContext Hook

```tsx
import { useErrorContext } from '@/lib/error-context';
import { formatApiError } from '@/lib/error-formatter';

function MyComponent() {
  const { showError, dismissError, clearErrors } = useErrorContext();

  const handleAction = async () => {
    try {
      await doSomething();
    } catch (err) {
      const formatted = formatApiError(err);
      const errorId = showError(formatted, {
        duration: 5000,      // Auto-dismiss after 5 seconds
        dismissible: true,   // Show close button
      });

      // Later, manually dismiss if needed
      dismissError(errorId);
    }
  };

  return <button onClick={handleAction}>Do Action</button>;
}
```

### useError Hook

For component-level error management without global context:

```tsx
import { useError } from '@/lib/error-context';
import { formatUploadError } from '@/lib/error-formatter';

function SessionUploader() {
  const { error, setError, clearError } = useError();

  const handleUpload = async (file: File) => {
    try {
      await uploadSession(file);
    } catch (err) {
      const formatted = formatUploadError(err);
      setError(formatted);
    }
  };

  return (
    <>
      {error && (
        <ErrorMessage
          message={error.message}
          description={error.description}
          variant="alert"
          onDismiss={clearError}
        />
      )}
    </>
  );
}
```

## Real-World Examples

### File Upload with Error Handling

```tsx
'use client';

import { useState } from 'react';
import { uploadSession } from '@/lib/api';
import { ErrorMessage } from '@/components/ui/error-message';
import { formatUploadError } from '@/lib/error-formatter';
import type { FormattedError } from '@/lib/error-formatter';

function SessionUploader({ patientId }: { patientId: string }) {
  const [error, setError] = useState<FormattedError | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = async (file: File) => {
    // Validate file locally
    if (file.size > 100 * 1024 * 1024) {
      setError({
        message: 'File too large',
        description: `File is ${(file.size / 1024 / 1024).toFixed(1)}MB. Max 100MB.`,
        suggestion: 'Try a smaller file',
        severity: 'error',
        retryable: false,
      });
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const session = await uploadSession(patientId, file);
      // Success!
    } catch (err) {
      // Format and display error
      const formatted = formatUploadError(err);
      setError(formatted);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {error && (
        <ErrorMessage
          message={error.message}
          description={error.description}
          variant="alert"
          severity={error.severity}
          dismissible
          onDismiss={() => setError(null)}
          action={
            error.retryable
              ? {
                  label: 'Try Again',
                  onClick: () => {
                    // Trigger upload again
                  },
                }
              : undefined
          }
        />
      )}
      {/* Upload UI */}
    </>
  );
}
```

### Authentication Form with Validation

```tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { ErrorMessage } from '@/components/ui/error-message';
import { formatAuthError } from '@/lib/error-formatter';
import type { FormattedError } from '@/lib/error-formatter';
import type { FailureResult } from '@/lib/api-types';

function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<FormattedError | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (!email || !password) {
      setError({
        message: 'Missing credentials',
        description: 'Please enter both email and password',
        severity: 'error',
        retryable: false,
      });
      return;
    }

    setIsLoading(true);

    try {
      await login(email, password);
      // Success - redirect in useEffect
    } catch (err) {
      if (err instanceof Error) {
        const formatted = formatAuthError({
          success: false,
          status: 401,
          error: err.message,
        } as FailureResult);
        setError(formatted);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <ErrorMessage
          message={error.message}
          description={error.description}
          variant="alert"
          severity={error.severity}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}
      {/* Form fields */}
    </form>
  );
}
```

### Data Fetching with Error Handling

```tsx
'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { ErrorMessageBanner } from '@/components/ui/error-message';
import { formatDataFetchError } from '@/lib/error-formatter';
import type { FormattedError } from '@/lib/error-formatter';

function PatientList() {
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState<FormattedError | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchPatients = async () => {
      setIsLoading(true);
      setError(null);

      const result = await apiClient.get('/api/patients/');

      if (result.success) {
        setPatients(result.data);
      } else {
        const formatted = formatDataFetchError(result);
        setError(formatted);
      }

      setIsLoading(false);
    };

    fetchPatients();
  }, []);

  if (isLoading) return <div>Loading...</div>;

  return (
    <>
      {error && (
        <ErrorMessageBanner
          message={error.message}
          description={error.description}
          severity={error.severity}
          action={{
            label: 'Reload',
            onClick: () => window.location.reload(),
          }}
        />
      )}
      {/* Patient list */}
    </>
  );
}
```

## Best Practices

1. **Always format errors for users** - Don't show raw API errors
2. **Include suggestions** - Tell users what they can do to fix the problem
3. **Use appropriate variants** - Choose the right component for the context
4. **Handle specific error types** - Check for common errors first
5. **Allow retries** - Make it easy for users to try again with `retryable` flag
6. **Field-level errors** - Display validation errors at the field level when possible
7. **Auto-dismiss toasts** - Toast errors should auto-dismiss after a few seconds
8. **Provide actionable feedback** - Help users understand what went wrong

## Testing Error States

Mock errors for testing:

```tsx
import { ErrorMessage } from '@/components/ui/error-message';

// Test error display
<ErrorMessage
  message="Test error message"
  description="This is a test error"
  variant="alert"
  severity="error"
  dismissible
/>

// Test warning
<ErrorMessage
  message="Warning message"
  severity="warning"
  variant="banner"
/>

// Test info
<ErrorMessage
  message="Info message"
  severity="info"
  variant="toast"
/>
```

## Troubleshooting

### Error message doesn't dismiss

Ensure `onDismiss` callback is provided and sets the error to null:

```tsx
onDismiss={() => setError(null)} // ✓ Correct
onDismiss={setError}             // ✗ Wrong
```

### Custom error format not working

The error formatter handles most cases, but for custom errors:

```tsx
const customError: FormattedError = {
  message: 'Custom error',
  description: 'Your custom description',
  suggestion: 'What to do',
  severity: 'error',
  retryable: true,
};

setError(customError);
```

### Field errors not displaying

For validation errors, extract field errors:

```tsx
const formatted = formatApiError(result);
if (formatted.fieldErrors) {
  // Display field-specific errors
  Object.entries(formatted.fieldErrors).forEach(([field, error]) => {
    console.log(`${field}: ${error}`);
  });
}
```

## API Reference

### ErrorMessage Props

```typescript
interface ErrorMessageProps {
  message: string;                           // Required
  description?: string;
  variant?: 'inline' | 'alert' | 'toast' | 'banner'; // Default: 'inline'
  severity?: 'error' | 'warning' | 'info';  // Default: 'error'
  dismissible?: boolean;                    // Default: false
  onDismiss?: () => void;
  action?: { label: string; onClick: () => void };
  className?: string;
}
```

### FormattedError Interface

```typescript
interface FormattedError {
  message: string;
  description?: string;
  suggestion?: string;
  severity: 'error' | 'warning' | 'info';
  retryable: boolean;
  fieldErrors?: Record<string, string>;
}
```

## Further Reading

- [Error Component Source](/components/ui/error-message.tsx)
- [Error Formatter Source](/lib/error-formatter.ts)
- [Error Context Source](/lib/error-context.tsx)
