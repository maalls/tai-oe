-- Purchase Order / Bon de commande
CREATE TABLE IF NOT EXISTS purchase_order (
  document_id              uuid PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
  po_number                text,
  ordered_at               timestamptz,
  requested_delivery_date  date
);

CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_order(po_number);
