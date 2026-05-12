CREATE TABLE IF NOT EXISTS family (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  type        text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_family_name ON family USING btree (name);
CREATE INDEX IF NOT EXISTS idx_family_type ON family (type);
