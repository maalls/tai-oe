CREATE TABLE IF NOT EXISTS brand (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text NOT NULL,
  legal_name      text,
  website         text,
  email           text,
  phone           text,
  marque          text NOT NULL,
  address_line1   text,
  address_line2   text,
  city            text,
  state           text,
  postal_code     text,
  country_code    char(2) DEFAULT 'FR',
  vendor_id       uuid NOT NULL REFERENCES vendor(id) ON DELETE RESTRICT,
  notes           text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  minimum_margin  numeric(5,2) DEFAULT 0.00,
  target_margin   numeric(5,2) DEFAULT 0.00,
  CONSTRAINT brand_vendor_name_key UNIQUE (vendor_id, name)
);

CREATE INDEX IF NOT EXISTS idx_brand_name ON brand USING btree (name);
CREATE INDEX IF NOT EXISTS idx_brand_email ON brand (email);
CREATE INDEX IF NOT EXISTS idx_brand_vendor_id ON brand (vendor_id);
