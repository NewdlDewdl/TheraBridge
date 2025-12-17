# Form Validation - Usage Examples

## Example 1: Basic Email Field

```tsx
import { FormField } from '@/components/ui/form-field';
import { emailRules } from '@/lib/validation';

export function EmailExample() {
  const [email, setEmail] = useState('');

  return (
    <FormField
      name="email"
      label="Email Address"
      type="email"
      value={email}
      onChange={setEmail}
      rules={emailRules}
      placeholder="you@example.com"
      validateOnChange
      showErrors
    />
  );
}
```

**User Experience:**
- Empty field: No feedback
- User types "abc": Shows error "Please enter a valid email address"
- User types "abc@": Still shows error
- User types "abc@example.com": Green checkmark appears, "Looks good!" message
- Field is now valid and can be submitted

---

## Example 2: Simple Login Form

```tsx
'use client';
import { useState, useEffect } from 'react';
import { FormField } from '@/components/ui/form-field';
import { Button } from '@/components/ui/button';
import { emailRules, passwordRules, validateFields, isAllValid } from '@/lib/validation';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [validation, setValidation] = useState({
    email: { isValid: true, errors: [], isDirty: false },
    password: { isValid: true, errors: [], isDirty: false },
  });
  const [isLoading, setIsLoading] = useState(false);

  // Validate on change
  useEffect(() => {
    const result = validateFields(
      { email, password },
      { email: emailRules, password: passwordRules }
    );
    setValidation(result);
  }, [email, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Check validation
    if (!isAllValid(validation)) {
      return; // Form invalid
    }

    setIsLoading(true);
    try {
      // Submit to server...
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      // Handle response...
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField
        name="email"
        label="Email"
        type="email"
        value={email}
        onChange={setEmail}
        rules={emailRules}
        validateOnChange
        showErrors
      />

      <FormField
        name="password"
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        rules={passwordRules}
        validateOnChange
        showErrors
      />

      <Button
        type="submit"
        className="w-full"
        disabled={isLoading || !isAllValid(validation)}
      >
        {isLoading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  );
}
```

---

## Example 3: Custom Validation Rules

```tsx
import { ValidationRule } from '@/lib/validation';
import { FormField } from '@/components/ui/form-field';

// Define custom validation rules for username
const usernameRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'Username is required',
  },
  {
    validate: (value) => value.length >= 3,
    message: 'Username must be at least 3 characters',
  },
  {
    validate: (value) => value.length <= 20,
    message: 'Username must be no more than 20 characters',
  },
  {
    validate: (value) => /^[a-zA-Z0-9_-]+$/.test(value),
    message: 'Username can only contain letters, numbers, hyphens, and underscores',
  },
];

export function UsernameField() {
  const [username, setUsername] = useState('');

  return (
    <FormField
      name="username"
      label="Username"
      value={username}
      onChange={setUsername}
      rules={usernameRules}
      placeholder="john_doe"
      validateOnChange
      showErrors
      helpText="3-20 characters, letters, numbers, hyphens, underscores"
    />
  );
}
```

---

## Example 4: Password Confirmation

```tsx
import { ValidationRule } from '@/lib/validation';
import { FormField } from '@/components/ui/form-field';
import { passwordStrongRules } from '@/lib/validation';

export function PasswordConfirmationForm() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Custom rule for password confirmation
  const confirmRules: ValidationRule[] = [
    {
      validate: (value) => value.length > 0,
      message: 'Please confirm your password',
    },
    {
      validate: (value) => value === password,
      message: 'Passwords do not match',
    },
  ];

  return (
    <div className="space-y-4">
      <FormField
        name="password"
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        rules={passwordStrongRules}
        validateOnChange
        showErrors
        helpText="8+ chars with uppercase, lowercase, and numbers"
      />

      <FormField
        name="confirmPassword"
        label="Confirm Password"
        type="password"
        value={confirmPassword}
        onChange={setConfirmPassword}
        rules={confirmRules}
        validateOnChange
        showErrors
      />
    </div>
  );
}
```

---

## Example 5: Conditional Validation

```tsx
import { ValidationRule } from '@/lib/validation';
import { FormField } from '@/components/ui/form-field';

interface OptionalFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
}

export function OptionalField({
  label,
  value,
  onChange,
  required = false,
}: OptionalFieldProps) {
  // Only require field if needed
  const rules: ValidationRule[] = required
    ? [
        {
          validate: (v) => v.trim().length > 0,
          message: `${label} is required`,
        },
      ]
    : [];

  return (
    <FormField
      name={label.toLowerCase()}
      label={label}
      value={value}
      onChange={onChange}
      rules={rules}
      validateOnChange
      showErrors
      required={required}
    />
  );
}

// Usage:
export function FormWithOptionalField() {
  const [phone, setPhone] = useState('');
  const [isPhoneRequired, setIsPhoneRequired] = useState(false);

  return (
    <div className="space-y-4">
      <label>
        <input
          type="checkbox"
          checked={isPhoneRequired}
          onChange={(e) => setIsPhoneRequired(e.target.checked)}
        />
        Require phone number
      </label>

      <OptionalField
        label="Phone"
        value={phone}
        onChange={setPhone}
        required={isPhoneRequired}
      />
    </div>
  );
}
```

---

## Example 6: Server-Side Error Integration

```tsx
'use client';
import { useState, useEffect } from 'react';
import { FormField } from '@/components/ui/form-field';
import { ValidationRule } from '@/lib/validation';
import { emailRules } from '@/lib/validation';

export function EmailWithServerValidation() {
  const [email, setEmail] = useState('');
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});

  // Combine client and server validation rules
  const combinedEmailRules: ValidationRule[] = [
    ...emailRules,
    {
      validate: (value) => !serverErrors.email,
      message: serverErrors.email || '',
    },
  ];

  const handleEmailChange = async (value: string) => {
    setEmail(value);

    // Check availability on server after user stops typing
    if (value.includes('@')) {
      const response = await fetch(
        `/api/check-email?email=${encodeURIComponent(value)}`
      );
      const data = await response.json();

      if (!data.available) {
        setServerErrors({ email: 'Email already in use' });
      } else {
        setServerErrors({});
      }
    }
  };

  return (
    <FormField
      name="email"
      label="Email"
      type="email"
      value={email}
      onChange={handleEmailChange}
      rules={combinedEmailRules}
      validateOnChange
      showErrors
    />
  );
}
```

---

## Example 7: Complex Multi-Field Form

```tsx
'use client';
import { useState, useEffect } from 'react';
import { FormField } from '@/components/ui/form-field';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  fullNameRules,
  emailRules,
  passwordStrongRules,
  validateFields,
  isAllValid,
} from '@/lib/validation';

interface SignupFormProps {
  onSuccess?: (data: any) => void;
}

export function ComplexSignupForm({ onSuccess }: SignupFormProps) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'user' | 'admin'>('user');
  const [validation, setValidation] = useState({
    fullName: { isValid: true, errors: [], isDirty: false },
    email: { isValid: true, errors: [], isDirty: false },
    password: { isValid: true, errors: [], isDirty: false },
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Multi-field validation
  useEffect(() => {
    const result = validateFields(
      { fullName, email, password },
      {
        fullName: fullNameRules,
        email: emailRules,
        password: passwordStrongRules,
      }
    );
    setValidation(result);
  }, [fullName, email, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAllValid(validation)) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fullName,
          email,
          password,
          role,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        onSuccess?.(data);
      } else {
        // Handle server errors
        const error = await response.json();
        console.error('Signup failed:', error);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const isFormValid = isAllValid(validation);

  return (
    <form onSubmit={handleSubmit} className="max-w-md space-y-5">
      <FormField
        name="fullName"
        label="Full Name"
        type="text"
        value={fullName}
        onChange={setFullName}
        rules={fullNameRules}
        placeholder="John Doe"
        required
        validateOnChange
        showErrors
      />

      <FormField
        name="email"
        label="Email Address"
        type="email"
        value={email}
        onChange={setEmail}
        rules={emailRules}
        placeholder="john@example.com"
        required
        validateOnChange
        showErrors
      />

      <FormField
        name="password"
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        rules={passwordStrongRules}
        placeholder="••••••••"
        required
        validateOnChange
        showErrors
        helpText="8+ chars with uppercase, lowercase, and numbers"
      />

      <div>
        <label className="block text-sm font-medium mb-2">Role</label>
        <Select value={role} onValueChange={(val) => setRole(val as 'user' | 'admin')}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="user">User</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={isSubmitting || !isFormValid}
      >
        {isSubmitting ? 'Creating Account...' : 'Sign Up'}
      </Button>
    </form>
  );
}
```

---

## Example 8: Reusable Form Component

```tsx
import { FormField } from '@/components/ui/form-field';
import { ValidationRule } from '@/lib/validation';

export interface FormFieldConfig {
  name: string;
  label: string;
  type: string;
  rules: ValidationRule[];
  placeholder?: string;
  helpText?: string;
  required?: boolean;
}

interface DynamicFormProps {
  fields: FormFieldConfig[];
  values: Record<string, string>;
  onValueChange: (name: string, value: string) => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
}

export function DynamicForm({
  fields,
  values,
  onValueChange,
  onSubmit,
  isSubmitting = false,
}: DynamicFormProps) {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(); }} className="space-y-4">
      {fields.map((field) => (
        <FormField
          key={field.name}
          name={field.name}
          label={field.label}
          type={field.type}
          value={values[field.name] || ''}
          onChange={(value) => onValueChange(field.name, value)}
          rules={field.rules}
          placeholder={field.placeholder}
          helpText={field.helpText}
          required={field.required}
          validateOnChange
          showErrors
        />
      ))}

      <button
        type="submit"
        disabled={isSubmitting}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}

// Usage:
const loginFields: FormFieldConfig[] = [
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    rules: emailRules,
  },
  {
    name: 'password',
    label: 'Password',
    type: 'password',
    rules: passwordRules,
  },
];
```

---

## Validation States Visual Reference

```
IDLE STATE (Initial)
┌─────────────────────┐
│ Email              │  ← Gray border, no icon
│ you@example.com     │
└─────────────────────┘

TYPING - INVALID
┌─────────────────────┐
│ Email              │ ✗  ← Red border, alert icon
│ invalid.email       │
│ • Please enter a    │     Error message appears
│   valid email       │
└─────────────────────┘

TYPING - VALID
┌─────────────────────┐
│ Email              │ ✓  ← Green border, checkmark
│ test@example.com    │
│ Looks good!         │     Success message
└─────────────────────┘
```

---

## Testing Examples

```tsx
import { renderHook, act } from '@testing-library/react';
import { validateField, emailRules } from '@/lib/validation';

describe('Form Validation', () => {
  test('validates email correctly', () => {
    const { isValid, errors } = validateField(
      'invalid',
      emailRules
    );

    expect(isValid).toBe(false);
    expect(errors).toContain('Please enter a valid email address');
  });

  test('accepts valid emails', () => {
    const { isValid, errors } = validateField(
      'test@example.com',
      emailRules
    );

    expect(isValid).toBe(true);
    expect(errors).toHaveLength(0);
  });
});
```

