-- Email storage schema for multiple email providers (Gmail, Outlook, etc.)
-- Stores email, their classifications, and labels

-- Email table (provider-agnostic)
CREATE TABLE IF NOT EXISTS email (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Email provider
  provider TEXT NOT NULL,  -- 'gmail', 'outlook', 'yahoo', etc.
  provider_account_id TEXT,  -- Gmail user ID, Outlook user@domain, etc.
  
  -- Provider identifiers (unique per provider)
  provider_message_id TEXT NOT NULL,  -- Gmail: message_id, Outlook: id, etc.
  provider_thread_id TEXT,  -- Gmail: thread_id, Outlook: conversation_id, etc.
  provider_metadata JSONB,  -- Store provider-specific data
  
  -- Email metadata
  subject TEXT,
  from_email TEXT,
  from_name TEXT,
  from_raw TEXT,
  from_domain TEXT,
  from_local TEXT,
  from_is_valid BOOLEAN,
  to_email TEXT,
  cc_email TEXT,
  email_date TIMESTAMP,
  
  -- Email content (stored for reference)
  body_preview TEXT,  -- First 500 chars or preview
  body_full TEXT,     -- Full body (optional, can be large)
  
  -- Classification
  category TEXT,  -- RFP, RFQ, RFI, Bill, Quote, Proposal, Newsletter, Other
  category_suggestion TEXT,
  classification_reason TEXT,
  important BOOLEAN DEFAULT FALSE,
  is_classified BOOLEAN DEFAULT FALSE,
  classified_at TIMESTAMP,
  
  -- Relationships to contacts and accounts
  contact_id UUID REFERENCES contact(id) ON DELETE SET NULL,
  account_id UUID REFERENCES account(id) ON DELETE SET NULL,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT unique_provider_message UNIQUE(user_id, provider, provider_message_id)
);

-- Email labels table (many-to-many, provider-agnostic)
CREATE TABLE IF NOT EXISTS email_labels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID NOT NULL REFERENCES email(id) ON DELETE CASCADE,
  provider_label_id TEXT NOT NULL,  -- Gmail: label_id, Outlook: category, etc.
  label_name TEXT NOT NULL,  -- "INBOX", "SENT", "DRAFT", "Important", etc.
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT unique_email_label UNIQUE(email_id, provider_label_id)
);

-- Email attachments table (tracks provider attachment ids and stored files)
CREATE TABLE IF NOT EXISTS email_attachment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id UUID NOT NULL REFERENCES email(id) ON DELETE CASCADE,
  provider_attachment_id TEXT NOT NULL,
  filename TEXT,
  mime_type TEXT,
  size INTEGER,
  storage_path TEXT,
  created_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT unique_email_attachment UNIQUE(email_id, provider_attachment_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_email_user_id ON email(user_id);
CREATE INDEX IF NOT EXISTS idx_email_provider ON email(provider);
CREATE INDEX IF NOT EXISTS idx_email_provider_message_id ON email(provider_message_id);
CREATE INDEX IF NOT EXISTS idx_email_category ON email(category);
CREATE INDEX IF NOT EXISTS idx_email_classified ON email(is_classified);
CREATE INDEX IF NOT EXISTS idx_email_created_at ON email(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_contact_id ON email(contact_id);
CREATE INDEX IF NOT EXISTS idx_email_account_id ON email(account_id);
CREATE INDEX IF NOT EXISTS idx_email_labels_email_id ON email_labels(email_id);
CREATE INDEX IF NOT EXISTS idx_email_labels_label_name ON email_labels(label_name);
CREATE INDEX IF NOT EXISTS idx_email_attachment_email_id ON email_attachment(email_id);
CREATE INDEX IF NOT EXISTS idx_email_attachment_provider_attachment_id ON email_attachment(provider_attachment_id);

-- Enable RLS (Row Level Security)
ALTER TABLE email ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_labels ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_attachment ENABLE ROW LEVEL SECURITY;

-- Enable Realtime publication for email table (for frontend live updates)
ALTER PUBLICATION supabase_realtime ADD TABLE email;
ALTER PUBLICATION supabase_realtime ADD TABLE email_labels;
ALTER PUBLICATION supabase_realtime ADD TABLE email_attachment;

-- RLS Policies: Users can only see their own email
CREATE POLICY "Users can view own email" 
  ON email FOR SELECT 
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can insert own email" 
  ON email FOR INSERT 
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can update own email" 
  ON email FOR UPDATE 
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can delete own email" 
  ON email FOR DELETE 
  USING (user_id = (select auth.uid()));

-- Email labels policies
CREATE POLICY "Users can view own email labels" 
  ON email_labels FOR SELECT 
  USING (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can insert own email labels" 
  ON email_labels FOR INSERT 
  WITH CHECK (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can delete own email labels" 
  ON email_labels FOR DELETE 
  USING (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));

-- Email attachment policies
CREATE POLICY "Users can view own email attachments"
  ON email_attachment FOR SELECT
  USING (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can insert own email attachments"
  ON email_attachment FOR INSERT
  WITH CHECK (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));

CREATE POLICY "Users can delete own email attachments"
  ON email_attachment FOR DELETE
  USING (email_id IN (SELECT id FROM email WHERE user_id = (select auth.uid())));
