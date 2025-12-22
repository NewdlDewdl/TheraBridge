-- AI Chat System Schema
-- Supports both global chats and session-specific chats with full conversation history

-- Chat conversations table
CREATE TABLE IF NOT EXISTS chat_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES therapy_sessions(id) ON DELETE SET NULL,

  -- Auto-generated from first message, but editable
  title VARCHAR(255) NOT NULL DEFAULT 'New Chat',

  -- Metadata
  message_count INTEGER DEFAULT 0,
  last_message_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,

  -- Message content
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,

  -- Metadata for analytics and debugging
  metadata JSONB DEFAULT '{}'::jsonb,
  -- Stores: { tokens: number, model: string, processing_time_ms: number, context_used: boolean }

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rate limiting table (tracks daily message usage)
CREATE TABLE IF NOT EXISTS chat_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  message_count INTEGER DEFAULT 0,

  -- Ensure one record per user per day
  UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_session_id ON chat_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_updated_at ON chat_conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_usage_user_date ON chat_usage(user_id, date);

-- Function to auto-update conversation updated_at and message_count
CREATE OR REPLACE FUNCTION update_conversation_on_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE chat_conversations
  SET
    updated_at = NOW(),
    last_message_at = NOW(),
    message_count = message_count + 1
  WHERE id = NEW.conversation_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update conversation when message is added
DROP TRIGGER IF EXISTS on_message_created ON chat_messages;
CREATE TRIGGER on_message_created
  AFTER INSERT ON chat_messages
  FOR EACH ROW EXECUTE FUNCTION update_conversation_on_message();

-- Function to increment daily usage
CREATE OR REPLACE FUNCTION increment_chat_usage(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
  current_count INTEGER;
BEGIN
  -- Insert or update usage for today
  INSERT INTO chat_usage (user_id, date, message_count)
  VALUES (p_user_id, CURRENT_DATE, 1)
  ON CONFLICT (user_id, date)
  DO UPDATE SET message_count = chat_usage.message_count + 1;

  -- Return current count
  SELECT message_count INTO current_count
  FROM chat_usage
  WHERE user_id = p_user_id AND date = CURRENT_DATE;

  RETURN current_count;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) Policies
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_usage ENABLE ROW LEVEL SECURITY;

-- Users can only see their own conversations
CREATE POLICY chat_conversations_select_own ON chat_conversations
  FOR SELECT
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id)
  );

CREATE POLICY chat_conversations_insert_own ON chat_conversations
  FOR INSERT
  WITH CHECK (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id)
  );

CREATE POLICY chat_conversations_update_own ON chat_conversations
  FOR UPDATE
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id)
  );

CREATE POLICY chat_conversations_delete_own ON chat_conversations
  FOR DELETE
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id)
  );

-- Users can only see messages from their own conversations
CREATE POLICY chat_messages_select_own ON chat_messages
  FOR SELECT
  USING (
    conversation_id IN (
      SELECT cc.id FROM chat_conversations cc
      JOIN users u ON cc.user_id = u.id
      WHERE u.auth_id = auth.uid()
    )
  );

CREATE POLICY chat_messages_insert_own ON chat_messages
  FOR INSERT
  WITH CHECK (
    conversation_id IN (
      SELECT cc.id FROM chat_conversations cc
      JOIN users u ON cc.user_id = u.id
      WHERE u.auth_id = auth.uid()
    )
  );

-- Users can only see their own usage stats
CREATE POLICY chat_usage_select_own ON chat_usage
  FOR SELECT
  USING (
    auth.uid() IN (SELECT auth_id FROM users WHERE id = user_id)
  );

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Chat schema created successfully!';
  RAISE NOTICE '';
  RAISE NOTICE 'Tables created:';
  RAISE NOTICE '  - chat_conversations (stores conversation metadata)';
  RAISE NOTICE '  - chat_messages (stores individual messages)';
  RAISE NOTICE '  - chat_usage (tracks daily rate limits)';
  RAISE NOTICE '';
  RAISE NOTICE 'Features:';
  RAISE NOTICE '  ✓ Global chats + session-specific chats';
  RAISE NOTICE '  ✓ Auto-generated conversation titles (editable)';
  RAISE NOTICE '  ✓ Message count and last message tracking';
  RAISE NOTICE '  ✓ Rate limiting (50 messages/day per user)';
  RAISE NOTICE '  ✓ Full RLS security';
  RAISE NOTICE '';
  RAISE NOTICE 'Next: Run this SQL in Supabase Dashboard > SQL Editor';
END $$;
