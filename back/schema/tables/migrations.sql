-- Migrations tracking table
-- Keeps track of which migrations have been applied

CREATE TABLE IF NOT EXISTS migrations (
  id SERIAL PRIMARY KEY,
  migration_name TEXT NOT NULL UNIQUE,
  executed_at TIMESTAMP DEFAULT NOW(),
  checksum TEXT,  -- Optional: to verify migration file hasn't changed
  
  CONSTRAINT unique_migration_name UNIQUE(migration_name)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_migrations_name ON migrations(migration_name);

-- Enable RLS (optional - migrations are system-level)
ALTER TABLE migrations ENABLE ROW LEVEL SECURITY;

-- Allow service role to manage migrations
CREATE POLICY "Service role can manage migrations" 
  ON migrations FOR ALL 
  USING (true);
