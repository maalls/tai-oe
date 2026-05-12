ALTER TABLE public.profile
  ADD COLUMN IF NOT EXISTS imap_host text,
  ADD COLUMN IF NOT EXISTS imap_port integer,
  ADD COLUMN IF NOT EXISTS imap_username text,
  ADD COLUMN IF NOT EXISTS imap_password text,
  ADD COLUMN IF NOT EXISTS imap_mailbox text,
  ADD COLUMN IF NOT EXISTS imap_use_ssl boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS imap_enabled boolean NOT NULL DEFAULT false;