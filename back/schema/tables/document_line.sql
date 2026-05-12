-- ---------- DOCUMENT LINES ----------
CREATE TABLE IF NOT EXISTS document_line (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id            uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  position              integer NOT NULL DEFAULT 1,
  sku                   text,
  brand                 text,
  description           text NOT NULL,
  quantity              numeric(14,3) NOT NULL DEFAULT 1 CHECK (quantity >= 0),
  unit                  unit_type NOT NULL DEFAULT 'U',
  unit_price_excl_tax   numeric(14,4) NOT NULL DEFAULT 0,
  tax_rate              numeric(5,2) NOT NULL DEFAULT 20 CHECK (tax_rate >= 0 AND tax_rate <= 100),
  discount_rate         numeric(5,2) NOT NULL DEFAULT 0 CHECK (discount_rate >= 0 AND discount_rate <= 100),
  client_discount_rate  numeric(8,3) NOT NULL DEFAULT 0,
  line_total_excl_tax   numeric(14,2) NOT NULL DEFAULT 0,
  user_validated        uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  is_ref_verified       boolean NOT NULL DEFAULT false,
  is_quantity_verified  boolean NOT NULL DEFAULT false,
  is_price_verified     boolean NOT NULL DEFAULT false,
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_doc_line_doc ON document_line(document_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_doc_line_position ON document_line(document_id, position);
CREATE INDEX IF NOT EXISTS idx_doc_line_is_ref_verified ON document_line(is_ref_verified);
CREATE INDEX IF NOT EXISTS idx_doc_line_verified_status ON document_line(document_id, is_ref_verified);
