-- ---------- PRODUCT CATALOG ----------
CREATE TABLE IF NOT EXISTS product (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sku               text NOT NULL,
  name              text NOT NULL,
  price             numeric(12,4),
  batch             integer,
  fabdis_appli_date date,
  fabdis_edited_date date,
  brand_id          uuid NOT NULL REFERENCES brand(id) ON DELETE RESTRICT,
  default_unit      unit_type NOT NULL DEFAULT 'U',
  default_tax_rate  numeric(5,2) NOT NULL DEFAULT 20 CHECK (default_tax_rate >= 0 AND default_tax_rate <= 100),
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (brand_id, sku)
);
