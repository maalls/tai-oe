DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'product_brand_sku_unique'
  ) THEN
    ALTER TABLE product
      ADD CONSTRAINT product_brand_sku_unique UNIQUE (brand_id, sku);
  END IF;
END $$;
