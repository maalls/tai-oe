-- Allow negative client_discount_rate (e.g. markup above list price)
ALTER TABLE document_line
  DROP CONSTRAINT IF EXISTS document_line_client_discount_rate_check;

ALTER TABLE document_line
  ALTER COLUMN client_discount_rate TYPE NUMERIC(8,3);
