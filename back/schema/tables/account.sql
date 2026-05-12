-- ---------- CORE TABLES ----------
CREATE TABLE IF NOT EXISTS account (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text NOT NULL,
  vat_number      text,
  siret           text,
  address_line1   text,
  address_line2   text,
  postal_code     text,
  city            text,
  country_code    char(2) DEFAULT 'FR',
  payment_terms_default text, -- e.g. "30 days EOM"
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_account_name ON account USING btree (name);
