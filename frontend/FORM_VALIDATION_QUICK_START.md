# Form Validation - Quick Start Guide

## What's New?

Enhanced form validation UI for login/signup pages with:
- Real-time validation as users type
- Inline error messages
- Visual success states (green checkmarks)
- Better overall form UX

## Files Changed/Created

### New Files
1. **`lib/validation.ts`** - Validation rules and utilities (178 lines)
2. **`components/ui/form-field.tsx`** - High-level form field component (248 lines)
3. **`FORM_VALIDATION_GUIDE.md`** - Complete documentation
4. **`FORM_VALIDATION_QUICK_START.md`** - This file

### Updated Files
1. **`components/ui/input.tsx`** - Added validation state support (63 lines)
2. **`app/auth/login/page.tsx`** - Real-time validation + better UX (198 lines)
3. **`app/auth/signup/page.tsx`** - Enhanced with password strength validation (255 lines)

## Key Features

### Real-Time Validation
Fields validate as users type with immediate feedback:
```tsx
<FormField
  name="email"
  label="Email"
  type="email"
  value={email}
  onChange={setEmail}
  rules={emailRules}
  validateOnChange  // validates as user types
  showErrors        // shows error messages
  showValidationIcon // shows checkmark/alert icons
/>
```

### Visual Feedback
- **Valid field**: Green border + green checkmark
- **Invalid field**: Red border + red alert icon + error message
- **Success message**: "Looks good!" when field is complete

### Built-in Validation Rules

**Email:**
- Required
- Valid email format

**Password (Basic):**
- Required
- At least 8 characters

**Password (Strong - Signup only):**
- Required
- At least 8 characters
- Uppercase letters
- Lowercase letters
- Numbers

**Full Name:**
- Required
- At least 2 characters
- Only letters, spaces, hyphens, apostrophes

### Form Submit Control
Submit button is automatically disabled until form is valid:
```tsx
const isFormValid = isAllValid(fieldValidation);

<Button
  type="submit"
  disabled={isLoading || !isFormValid}
>
  Submit
</Button>
```

## Usage in Your Own Forms

### Step 1: Import utilities
```tsx
import { FormField } from '@/components/ui/form-field';
import { emailRules, passwordRules, validateFields, isAllValid } from '@/lib/validation';
```

### Step 2: Set up state
```tsx
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [fieldValidation, setFieldValidation] = useState({
  email: { isValid: true, errors: [], isDirty: false },
  password: { isValid: true, errors: [], isDirty: false },
});
```

### Step 3: Update validation on change
```tsx
useEffect(() => {
  const validation = validateFields(
    { email, password },
    { email: emailRules, password: passwordRules }
  );
  setFieldValidation(validation);
}, [email, password]);
```

### Step 4: Use FormField components
```tsx
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
```

### Step 5: Validate before submit
```tsx
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();

  if (!isAllValid(fieldValidation)) {
    return; // Form invalid, don't submit
  }

  // Submit form...
};
```

## Creating Custom Validation Rules

```tsx
import { ValidationRule } from '@/lib/validation';

const phoneRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'Phone number is required',
  },
  {
    validate: (value) => /^\d{10}$/.test(value.replace(/\D/g, '')),
    message: 'Phone number must be 10 digits',
  },
];
```

## Common Scenarios

### Password Confirmation
```tsx
const passwordConfirmRules: ValidationRule[] = [
  {
    validate: (value) => value === password,
    message: 'Passwords do not match',
  },
];

<FormField
  name="confirmPassword"
  label="Confirm Password"
  type="password"
  value={confirmPassword}
  onChange={setConfirmPassword}
  rules={passwordConfirmRules}
  validateOnChange
/>
```

### Optional Field with Conditional Rules
```tsx
const rules = optional ? [] : [
  {
    validate: (value) => value.trim().length > 0,
    message: 'This field is required',
  },
];

<FormField
  rules={rules}
  // ... other props
/>
```

## Testing Validation

```tsx
import { validateField, emailRules } from '@/lib/validation';

// Test valid email
const { isValid } = validateField('test@example.com', emailRules);
console.log(isValid); // true

// Test invalid email
const { isValid, errors } = validateField('invalid', emailRules);
console.log(isValid); // false
console.log(errors); // ["Please enter a valid email address"]
```

## FormField Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `name` | string | required | Field identifier |
| `label` | string | required | Label text |
| `type` | string | 'text' | HTML input type |
| `value` | string | required | Current value |
| `onChange` | function | required | Change handler |
| `rules` | ValidationRule[] | [] | Validation rules |
| `validateOnChange` | boolean | true | Real-time validation |
| `validateOnBlur` | boolean | true | Validate on blur |
| `showErrors` | boolean | true | Show error messages |
| `showValidationIcon` | boolean | true | Show checkmark/alert |
| `required` | boolean | false | Show required indicator |
| `helpText` | string | - | Help text below field |
| `disabled` | boolean | false | Disabled state |

## Validation Utilities

```tsx
import {
  validateField,        // Validate single field
  validateFields,       // Validate multiple fields at once
  isAllValid,          // Check if all fields valid
  getFirstError,       // Get first error message
  hasError,            // Check if field has error
  isSuccess,           // Check if field is valid
} from '@/lib/validation';
```

## Browser Support

Works in all modern browsers:
- Chrome/Edge
- Firefox
- Safari
- Mobile browsers

## See Also

- `FORM_VALIDATION_GUIDE.md` - Detailed documentation with examples
- `app/auth/login/page.tsx` - Login implementation example
- `app/auth/signup/page.tsx` - Signup implementation example
