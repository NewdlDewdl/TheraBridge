# Apply Chat Schema Migration

This guide walks you through applying the AI chat database schema to your Supabase project.

## Prerequisites

- Supabase project created (✅ Already configured)
- Project URL: `https://rfckpldoohyjctrqxmiv.supabase.co`

## Option 1: Supabase Dashboard (Recommended)

### Step 1: Access SQL Editor

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `rfckpldoohyjctrqxmiv`
3. Click **SQL Editor** in the left sidebar

### Step 2: Run Migration

1. Click **New Query**
2. Copy the entire contents of `/supabase/chat-schema.sql`
3. Paste into the SQL editor
4. Click **Run** (or press Cmd/Ctrl + Enter)

### Step 3: Verify Success

You should see success messages:
```
✅ Chat schema created successfully!

Tables created:
  - chat_conversations (stores conversation metadata)
  - chat_messages (stores individual messages)
  - chat_usage (tracks daily rate limits)

Features:
  ✓ Global chats + session-specific chats
  ✓ Auto-generated conversation titles (editable)
  ✓ Message count and last message tracking
  ✓ Rate limiting (50 messages/day per user)
  ✓ Full RLS security
```

### Step 4: Verify Tables Created

In the Supabase Dashboard:
1. Go to **Table Editor**
2. You should see 3 new tables:
   - `chat_conversations`
   - `chat_messages`
   - `chat_usage`

## Option 2: Supabase CLI (Alternative)

If you have Supabase CLI installed:

```bash
# Navigate to project root
cd /Users/vishnuanapalli/Desktop/Rohin\ \&\ Vish\ Global\ Domination/peerbridge\ proj/

# Apply migration
supabase db push supabase/chat-schema.sql
```

## Tables Created

### 1. chat_conversations
Stores conversation metadata:
- `id` - UUID primary key
- `user_id` - Foreign key to users table
- `session_id` - Optional foreign key to therapy_sessions (null for global chats)
- `title` - Auto-generated from first message, editable
- `message_count` - Auto-incremented via trigger
- `last_message_at` - Auto-updated via trigger
- `created_at`, `updated_at` - Timestamps

### 2. chat_messages
Stores individual messages:
- `id` - UUID primary key
- `conversation_id` - Foreign key to chat_conversations
- `role` - 'user', 'assistant', or 'system'
- `content` - Message text
- `metadata` - JSONB field for tokens, model, processing time, etc.
- `created_at` - Timestamp

### 3. chat_usage
Rate limiting tracker:
- `id` - UUID primary key
- `user_id` - Foreign key to users table
- `date` - Current date (UNIQUE constraint per user)
- `message_count` - Daily message count

## Features Enabled

✅ **Automatic triggers**:
- `update_conversation_on_message()` - Auto-updates conversation metadata when message is inserted

✅ **Rate limiting function**:
- `increment_chat_usage(user_id)` - Increments daily usage and returns current count

✅ **Row Level Security (RLS)**:
- Users can only access their own conversations and messages
- Enforced at database level for security

## Troubleshooting

### Error: "relation already exists"
The tables might already exist. You can either:
1. Drop the existing tables first (⚠️ This deletes all data):
   ```sql
   DROP TABLE IF EXISTS chat_messages CASCADE;
   DROP TABLE IF EXISTS chat_conversations CASCADE;
   DROP TABLE IF EXISTS chat_usage CASCADE;
   ```
2. Or skip the migration if tables are already correct

### Error: "permission denied"
Make sure you're logged in to the correct Supabase project and have admin permissions.

### RLS Errors
If you get RLS errors when testing the chat:
1. Ensure you're authenticated (logged in user)
2. Check that `auth.uid()` matches a user in the `users` table
3. Verify the `users` table has an `auth_id` column linking to `auth.users`

## Next Steps

After applying the migration:
1. ✅ Test the chat API endpoint: `POST /api/chat`
2. ✅ Verify streaming responses work
3. ✅ Check rate limiting (50 messages/day)
4. ✅ Confirm conversation history persists
5. ✅ Test auto-title generation

## Testing the Migration

Run this SQL query to verify everything is set up:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'chat_%';

-- Should return:
-- chat_conversations
-- chat_messages
-- chat_usage

-- Check triggers exist
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'on_message_created';

-- Check RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename LIKE 'chat_%';
```

All set! Your AI chat database is ready. 🚀
