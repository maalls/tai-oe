ALTER TABLE product
  ADD COLUMN IF NOT EXISTS price numeric(12,4);
