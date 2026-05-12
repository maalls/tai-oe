-- Add markup_rate column to document_line table
ALTER TABLE document_line
  ADD COLUMN IF NOT EXISTS markup_rate numeric(5,2) DEFAULT 0 CHECK (markup_rate >= 0);

COMMENT ON COLUMN document_line.markup_rate IS 'Markup rate as a percentage (e.g., 15.5 for 15.5%)';
