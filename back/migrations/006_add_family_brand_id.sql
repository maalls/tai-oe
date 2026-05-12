ALTER TABLE family
  ADD COLUMN IF NOT EXISTS brand_id uuid;

UPDATE family
SET brand_id = brand.id
FROM brand
WHERE family.brand_id IS NULL
  AND brand.id IS NOT NULL
  AND brand.name = family.name;

ALTER TABLE family
  ALTER COLUMN brand_id SET NOT NULL;

ALTER TABLE family
  ADD CONSTRAINT family_brand_id_fkey
  FOREIGN KEY (brand_id) REFERENCES brand(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_family_brand ON family (brand_id);
