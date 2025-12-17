# Error Handling Quick Reference

## Components

### ErrorMessage
Main error display component with 4 variants and 3 severity levels.

```tsx
import { ErrorMessage } from '@/components/ui/error-message';

<ErrorMessage
  message="Error title"
  description="Optional details"
  variant="alert" // inline | alert | toast | banner
  severity="error" // error | warning | info
  dismissible={true}
  onDismiss={() => setError(null)}
  action={{ label: 'Retry', onClick: () => retry() }}
/>
```

### Quick Variants
```tsx
import {
  ErrorMessageInline,
  ErrorMessageAlert,
  ErrorMessageToast,
  ErrorMessageBanner,
} from '@/components/ui/error-message';

// Equivalent to ErrorMessage with variant pre-set
<ErrorMessageAlert message="Error" />
<ErrorMessageToast message="Error" />
<ErrorMessageInline message="Error" />
<ErrorMessageBanner message="Error" />
```

## Formatters

### formatApiError
Convert any API error to user-friendly format:

```tsx
import { formatApiError } from '@/lib/error-formatter';

try {
  const result = await apiClient.get('/endpoint');
  if (!result.success) {
    const error = formatApiError(result);
    // error.message: "Patient not found"
    // error.suggestion: "Check the patient ID and try again"
    // error.retryable: true
  }
} catch (err) {
  const error = formatApiError(err);
}
```

### Context-Specific Formatters

```tsx
import {
  formatUploadError,
  formatAuthError,
  formatDataFetchError,
  formatValidationError,
} from '@/lib/error-formatter';

// Use based on context
const uploadErr = formatUploadError(error);      // File uploads
const authErr = formatAuthError(error);           // Authentication
const fetchErr = formatDataFetchError(error);     // Data loading
const validErr = formatValidationError(response); // Form validation
```

## Component Patterns

### Pattern 1: Form Error Handling
```tsx
const [error, setError] = useState<FormattedError | null>(null);

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError(null);

  try {
    await submit();
  } catch (err) {
    setError(formatAuthError(err));
  }
};

return (
  <>
    {error && (
      <ErrorMessage
        message={error.message}
        description={error.description}
        variant="alert"
        onDismiss={() => setError(null)}
      />
    )}
    <form onSubmit={handleSubmit}>
      {/* form fields */}
    </form>
  </>
);
```

### Pattern 2: Upload Error Handling
```tsx
const [error, setError] = useState<FormattedError | null>(null);
const [isUploading, setIsUploading] = useState(false);

const handleUpload = async (file: File) => {
  setIsUploading(true);
  setError(null);

  try {
    await uploadSession(patientId, file);
  } catch (err) {
    setError(formatUploadError(err));
  } finally {
    setIsUploading(false);
  }
};

return (
  <>
    {error && (
      <ErrorMessage
        message={error.message}
        description={error.description}
        variant="inline"
        dismissible
        onDismiss={() => setError(null)}
      />
    )}
    <UploadUI onUpload={handleUpload} disabled={isUploading} />
  </>
);
```

### Pattern 3: Page Error Handling
```tsx
const { data, isError, error } = usePatients();

if (isError) {
  return (
    <ErrorMessageAlert
      message="Failed to load patients"
      description={error?.message}
      action={{
        label: 'Retry',
        onClick: () => window.location.reload(),
      }}
    />
  );
}

return <PatientList patients={data} />;
```

## Error Types

### FormattedError Interface
```typescript
interface FormattedError {
  message: string;           // Main error message
  description?: string;      // Additional details
  suggestion?: string;       // What to do about it
  severity: 'error' | 'warning' | 'info';
  retryable: boolean;        // Can user retry?
  fieldErrors?: Record<string, string>; // Field-specific errors
}
```

## Common Error Messages

### Upload Errors
| Error | Message | Suggestion |
|-------|---------|-----------|
| File too large | "File size must be less than 100MB" | Try a smaller file |
| Invalid type | "Please upload audio or video file" | MP3, WAV, M4A, etc. |
| Server error | "Server error during upload" | Try uploading again |

### Authentication Errors
| Error | Message | Suggestion |
|-------|---------|-----------|
| Invalid credentials | "Email or password is incorrect" | Check and try again |
| Email registered | "Email already registered" | Try logging in |
| Network error | "Unable to connect" | Check internet |

### Data Errors
| Error | Message | Suggestion |
|-------|---------|-----------|
| Not found | "Resource not found" | Check the ID |
| Forbidden | "Access denied" | Contact admin |
| Timeout | "Request timed out" | Try again |

## Hooks

### useErrorContext
Global error management:

```tsx
import { useErrorContext } from '@/lib/error-context';

function MyComponent() {
  const { showError, dismissError, clearErrors } = useErrorContext();

  const handleAction = async () => {
    try {
      await doSomething();
    } catch (err) {
      const formatted = formatApiError(err);
      const errorId = showError(formatted, { duration: 5000 });
      // Later: dismissError(errorId);
    }
  };

  return <button onClick={handleAction}>Action</button>;
}
```

### useError
Component-level error management:

```tsx
import { useError } from '@/lib/error-context';

function MyComponent() {
  const { error, setError, clearError } = useError();

  const handleAction = async () => {
    try {
      await doSomething();
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  return (
    <>
      {error && (
        <ErrorMessage
          message={error.message}
          description={error.description}
          onDismiss={clearError}
        />
      )}
    </>
  );
}
```

## Setup

### Wrap App with ErrorProvider
```tsx
import { ErrorProvider } from '@/lib/error-context';

export default function RootLayout() {
  return (
    <ErrorProvider>
      <YourApp />
    </ErrorProvider>
  );
}
```

## Examples by Use Case

### Login Form
```tsx
const [error, setError] = useState<FormattedError | null>(null);

const handleLogin = async (email: string, password: string) => {
  try {
    await login(email, password);
    // Success - redirect
  } catch (err) {
    setError(formatAuthError(err));
  }
};

return (
  <>
    {error && (
      <ErrorMessageAlert
        message={error.message}
        description={error.description}
        dismissible
        onDismiss={() => setError(null)}
      />
    )}
    <LoginForm onSubmit={handleLogin} />
  </>
);
```

### File Upload
```tsx
const [error, setError] = useState<FormattedError | null>(null);

const handleUpload = async (file: File) => {
  try {
    await uploadFile(file);
  } catch (err) {
    setError(formatUploadError(err));
  }
};

return (
  <>
    {error && (
      <ErrorMessageInline
        message={error.message}
        description={error.description}
        action={
          error.retryable
            ? { label: 'Try Again', onClick: () => handleUpload(file) }
            : undefined
        }
      />
    )}
    <FileUpload onUpload={handleUpload} />
  </>
);
```

### Data Loading
```tsx
const { data, isLoading, isError } = useData();

if (isError) {
  return (
    <ErrorMessageAlert
      message="Failed to load data"
      description="Please try refreshing the page"
      action={{
        label: 'Refresh',
        onClick: () => window.location.reload(),
      }}
    />
  );
}

if (isLoading) return <LoadingSpinner />;

return <DataDisplay data={data} />;
```

## Tips & Best Practices

1. **Always show description** - Explain what happened
2. **Provide suggestion** - Tell user what to do next
3. **Use retryable flag** - Show retry button if applicable
4. **Match variant to context** - Alert for pages, inline for forms, toast for notifications
5. **Dismiss automatically** - Toasts should auto-dismiss after 3-5 seconds
6. **Include action button** - Help users recover from errors
7. **Handle field errors** - Display validation errors at field level
8. **Test error states** - Mock errors to test user experience

## More Information

- **Full Guide:** `/ERROR_HANDLING_GUIDE.md`
- **Implementation Details:** `/ERROR_HANDLING_IMPLEMENTATION.md`
- **Component Source:** `/components/ui/error-message.tsx`
- **Formatter Source:** `/lib/error-formatter.ts`
- **Context Source:** `/lib/error-context.tsx`
