ALTER TABLE brand
  ADD COLUMN IF NOT EXISTS marque text;

CREATE INDEX IF NOT EXISTS idx_brand_marque ON brand (marque);
