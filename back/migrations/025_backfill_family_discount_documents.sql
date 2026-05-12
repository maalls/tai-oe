WITH target_brands AS (
  SELECT DISTINCT b.id, b.name
  FROM brand b
  JOIN family f ON f.brand_id = b.id
  WHERE f.document_id IS NULL
), inserted AS (
  INSERT INTO document (
    opportunity_id,
    channel,
    type,
    status,
    title,
    external_ref
  )
  SELECT
    NULL,
    'OTHER',
    'FAMILY_DISCOUNT',
    'DRAFT',
    'FAB-DIS families - ' || name,
    id::text
  FROM target_brands
  RETURNING id, external_ref
)
UPDATE family f
SET document_id = i.id
FROM inserted i
WHERE f.document_id IS NULL
  AND f.brand_id::text = i.external_ref;

ALTER TABLE family
ALTER COLUMN document_id SET NOT NULL;
