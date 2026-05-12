CREATE TABLE IF NOT EXISTS product_family (
  product_id  uuid NOT NULL REFERENCES product(id) ON DELETE CASCADE,
  family_id   uuid NOT NULL REFERENCES family(id) ON DELETE CASCADE,
  PRIMARY KEY (product_id, family_id)
);

CREATE INDEX IF NOT EXISTS idx_product_family_product ON product_family (product_id);
CREATE INDEX IF NOT EXISTS idx_product_family_family ON product_family (family_id);
