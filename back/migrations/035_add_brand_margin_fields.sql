ALTER TABLE brand
  ADD COLUMN IF NOT EXISTS minimum_margin numeric(5,2) DEFAULT 0.00,
  ADD COLUMN IF NOT EXISTS target_margin numeric(5,2) DEFAULT 0.00;

UPDATE brand
SET
  minimum_margin = COALESCE(minimum_margin, 0.00),
  target_margin = COALESCE(target_margin, 0.00)
WHERE minimum_margin IS NULL OR target_margin IS NULL;