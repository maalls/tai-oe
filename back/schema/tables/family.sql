CREATE TABLE IF NOT EXISTS family (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id    uuid NOT NULL REFERENCES brand(id) ON DELETE CASCADE,
  name        text,
  code        text,
  type        text,
  product_code text,
  quantity    numeric(14,3),
  discount    numeric(5,2),
  unit        text,
  packing     text,
  lead_time_week integer,
  net_price   numeric(14,4),
  minimum_margin numeric(5,2) DEFAULT 0.00,
  target_margin  numeric(5,2) DEFAULT 0.00,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_family_name ON family USING btree (name);
CREATE INDEX IF NOT EXISTS idx_family_code ON family (code);
CREATE INDEX IF NOT EXISTS idx_family_type ON family (type);
CREATE INDEX IF NOT EXISTS idx_family_brand ON family (brand_id);

ALTER TABLE family
ADD CONSTRAINT family_brand_code_product_code_unique
UNIQUE (brand_id, code, product_code);

-- Product to family mapping (many-to-many)
CREATE TABLE IF NOT EXISTS product_family (
  product_id  uuid NOT NULL REFERENCES product(id) ON DELETE CASCADE,
  family_id   uuid NOT NULL REFERENCES family(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (product_id, family_id)
);

CREATE INDEX IF NOT EXISTS idx_product_family_product ON product_family (product_id);
CREATE INDEX IF NOT EXISTS idx_product_family_family ON product_family (family_id);
