-- ---------- HELPERS / DATA INTEGRITY ----------
-- Optional: ensure specialized tables match document.type
-- Implement via triggers to enforce (QUOTE->quote table etc.)

CREATE OR REPLACE FUNCTION enforce_document_type_for_specialization()
RETURNS trigger AS $$
DECLARE doc_type document_type;
BEGIN
  SELECT type INTO doc_type FROM document WHERE id = NEW.document_id;

  IF TG_TABLE_NAME = 'quote' AND doc_type <> 'QUOTE' THEN
    RAISE EXCEPTION 'quote.document_id must reference a document of type QUOTE (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'purchase_order' AND doc_type <> 'PO' THEN
    RAISE EXCEPTION 'purchase_order.document_id must reference a document of type PO (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'contract' AND doc_type <> 'CONTRACT' THEN
    RAISE EXCEPTION 'contract.document_id must reference a document of type CONTRACT (got %)', doc_type;
  ELSIF TG_TABLE_NAME = 'invoice' AND doc_type <> 'INVOICE' THEN
    RAISE EXCEPTION 'invoice.document_id must reference a document of type INVOICE (got %)', doc_type;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_quote_type ON quote;
CREATE TRIGGER trg_quote_type
BEFORE INSERT OR UPDATE ON quote
FOR EACH ROW EXECUTE FUNCTION enforce_document_type_for_specialization();

DROP TRIGGER IF EXISTS trg_po_type ON purchase_order;
CREATE TRIGGER trg_po_type
BEFORE INSERT OR UPDATE ON purchase_order
FOR EACH ROW EXECUTE FUNCTION enforce_document_type_for_specialization();

DROP TRIGGER IF EXISTS trg_contract_type ON contract;
CREATE TRIGGER trg_contract_type
BEFORE INSERT OR UPDATE ON contract
FOR EACH ROW EXECUTE FUNCTION enforce_document_type_for_specialization();

DROP TRIGGER IF EXISTS trg_invoice_type ON invoice;
CREATE TRIGGER trg_invoice_type
BEFORE INSERT OR UPDATE ON invoice
FOR EACH ROW EXECUTE FUNCTION enforce_document_type_for_specialization();
