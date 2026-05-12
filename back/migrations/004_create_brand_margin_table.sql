CREATE TABLE IF NOT EXISTS brand_margin (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id    uuid NOT NULL REFERENCES brand(id) ON DELETE CASCADE,
  contract_id uuid NOT NULL REFERENCES contract(document_id) ON DELETE CASCADE,
  margin      numeric(12,4) NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (brand_id, contract_id)
);

CREATE INDEX IF NOT EXISTS idx_brand_margin_brand ON brand_margin(brand_id);
CREATE INDEX IF NOT EXISTS idx_brand_margin_contract ON brand_margin(contract_id);
