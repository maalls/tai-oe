UPDATE brand
SET vendor_id = v.id
FROM vendor v
WHERE brand.vendor_id IS NULL
  AND brand.marque IS NOT NULL
  AND v.name IS NOT NULL
  AND brand.marque = v.name;
