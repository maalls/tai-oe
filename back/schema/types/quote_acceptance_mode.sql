DO $$ BEGIN
  CREATE TYPE quote_acceptance_mode AS ENUM ('SIGNED_QUOTE', 'EMAIL_OK', 'PORTAL_CLICK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
