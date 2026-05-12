CREATE TABLE IF NOT EXISTS brand (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text NOT NULL,
  legal_name      text,
  website         text,
  email           text,
  phone           text,
  address_line1   text,
  address_line2   text,
  city            text,
  state           text,
  postal_code     text,
  country_code    char(2) DEFAULT 'FR',
  notes           text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_brand_name ON brand USING btree (name);
CREATE INDEX IF NOT EXISTS idx_brand_email ON brand (email);
