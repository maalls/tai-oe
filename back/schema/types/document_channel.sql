DO $$ BEGIN
  CREATE TYPE document_channel AS ENUM ('EMAIL', 'PORTAL', 'PHONE', 'MANUAL', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
