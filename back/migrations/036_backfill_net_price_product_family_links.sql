-- Backfill product_family links for net_price families based on family.product_code -> product.sku.
-- Idempotent: running multiple times is safe.

-- 1) Create missing links.
INSERT INTO product_family (product_id, family_id)
SELECT p.id, f.id
FROM family f
JOIN product p
  ON btrim(p.sku) = btrim(f.product_code)
WHERE f.type = 'net_price'
  AND f.product_code IS NOT NULL
  AND btrim(f.product_code) <> ''
ON CONFLICT (product_id, family_id) DO NOTHING;

-- 2) For net_price families, keep only the link matching product_code when product exists.
DELETE FROM product_family pf
USING family f
JOIN product p_expected
  ON btrim(p_expected.sku) = btrim(f.product_code)
WHERE pf.family_id = f.id
  AND f.type = 'net_price'
  AND f.product_code IS NOT NULL
  AND btrim(f.product_code) <> ''
  AND pf.product_id <> p_expected.id;
