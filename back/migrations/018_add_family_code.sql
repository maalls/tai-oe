ALTER TABLE family
ADD COLUMN IF NOT EXISTS code text;

CREATE INDEX IF NOT EXISTS idx_family_code ON family (code);
