-- Sent Email storage schema
-- Stores outbound emails sent from the application (invoices, quotes, etc.)
-- Separate from the 'email' table which stores inbound emails for lead generation

CREATE TABLE IF NOT EXISTS sent_email (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Link to the document that was sent (invoice, quote, etc.)
  document_id UUID REFERENCES document(id) ON DELETE CASCADE,
  
  -- Link to opportunity if applicable
  opportunity_id UUID REFERENCES opportunity(id) ON DELETE SET NULL,
  
  -- Email details
  from_email TEXT NOT NULL,
  to_emails TEXT[] NOT NULL,  -- Array of recipient emails
  cc_emails TEXT[],           -- Array of CC emails
  bcc_emails TEXT[],          -- Array of BCC emails
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  
  -- Email provider details
  provider TEXT DEFAULT 'gmail',  -- 'gmail', 'sendgrid', 'smtp', etc.
  provider_message_id TEXT,       -- Gmail message ID, SendGrid message ID, etc.
  provider_metadata JSONB,        -- Store provider-specific data
  
  -- Delivery tracking
  status TEXT DEFAULT 'sent',  -- 'sent', 'delivered', 'opened', 'bounced', 'failed'
  sent_at TIMESTAMP DEFAULT NOW(),
  delivered_at TIMESTAMP,
  opened_at TIMESTAMP,
  bounced_at TIMESTAMP,
  error_message TEXT,
  
  -- Attachments info (for reference)
  attachment_names TEXT[],  -- List of attachment filenames
  
  -- User who sent the email
  sent_by_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sent_email_document_id ON sent_email(document_id);
CREATE INDEX IF NOT EXISTS idx_sent_email_opportunity_id ON sent_email(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_sent_email_sent_at ON sent_email(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_sent_email_status ON sent_email(status);
CREATE INDEX IF NOT EXISTS idx_sent_email_provider_message_id ON sent_email(provider_message_id);

-- Enable Row Level Security
ALTER TABLE sent_email ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Allow authenticated users to view all sent emails
CREATE POLICY "Authenticated users can view sent emails"
  ON sent_email FOR SELECT
  USING (auth.role() = 'authenticated');

-- Allow authenticated users to insert sent emails
CREATE POLICY "Authenticated users can insert sent emails"
  ON sent_email FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Allow service role to do everything (for backend operations)
CREATE POLICY "Service role has full access to sent emails"
  ON sent_email FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_sent_email_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sent_email_updated_at_trigger
  BEFORE UPDATE ON sent_email
  FOR EACH ROW
  EXECUTE FUNCTION update_sent_email_updated_at();
