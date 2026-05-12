-- Create brand entries from product.model and backfill product.brand_id
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'product' AND column_name = 'model'
  ) AND EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'product' AND column_name = 'brand_id'
  ) THEN
    INSERT INTO brand (name, created_at, updated_at)
    SELECT DISTINCT
      TRIM(p.model) AS name,
      now(),
      now()
    FROM product p
    WHERE p.model IS NOT NULL
      AND LENGTH(TRIM(p.model)) > 0
      AND NOT EXISTS (
        SELECT 1
        FROM brand b
        WHERE LOWER(b.name) = LOWER(TRIM(p.model))
      );

    UPDATE product p
    SET brand_id = b.id
    FROM brand b
    WHERE p.brand_id IS NULL
      AND p.model IS NOT NULL
      AND LENGTH(TRIM(p.model)) > 0
      AND LOWER(b.name) = LOWER(TRIM(p.model));
  END IF;
END $$;
