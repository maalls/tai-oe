ALTER TABLE product
  ADD COLUMN IF NOT EXISTS brand_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'product_brand_id_fkey'
  ) THEN
    ALTER TABLE product
      ADD CONSTRAINT product_brand_id_fkey
      FOREIGN KEY (brand_id) REFERENCES brand(id) ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_product_brand_id ON product (brand_id);
