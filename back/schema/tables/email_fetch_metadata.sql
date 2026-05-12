-- User email fetch metadata table
-- Tracks when emails were last fetched from providers

CREATE TABLE IF NOT EXISTS email_fetch_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,  -- 'gmail', 'outlook', etc.
  last_fetch_at TIMESTAMP DEFAULT NOW(),
  last_email_id TEXT,  -- Provider-specific ID of the last fetched email
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_user_provider UNIQUE(user_id, provider)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_email_fetch_metadata_user_provider ON email_fetch_metadata(user_id, provider);

-- Enable RLS
ALTER TABLE email_fetch_metadata ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own fetch metadata" 
  ON email_fetch_metadata FOR SELECT 
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can insert own fetch metadata" 
  ON email_fetch_metadata FOR INSERT 
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can update own fetch metadata" 
  ON email_fetch_metadata FOR UPDATE 
  USING (user_id = (select auth.uid()));
