-- Invoice / Facture
CREATE TABLE IF NOT EXISTS invoice (
  document_id        uuid PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
  invoice_number     text UNIQUE,
  due_date           date,
  paid_at            timestamptz,
  payment_status     invoice_payment_status NOT NULL DEFAULT 'UNPAID'
);

CREATE INDEX IF NOT EXISTS idx_invoice_due ON invoice(due_date);
CREATE INDEX IF NOT EXISTS idx_invoice_payment_status ON invoice(payment_status);
