DO $$ BEGIN
  CREATE TYPE unit_type AS ENUM ('U', 'M', 'H', 'DAY', 'PACK', 'KG', 'L');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
