-- Add total columns to document table for storing calculated totals
ALTER TABLE "document"
ADD COLUMN "total_excl_tax" NUMERIC(12, 2) DEFAULT 0,
ADD COLUMN "total_tax" NUMERIC(12, 2) DEFAULT 0,
ADD COLUMN "total_incl_tax" NUMERIC(12, 2) DEFAULT 0;

-- Ensure these columns are indexed for performance
CREATE INDEX idx_document_total_excl_tax ON "document"("total_excl_tax");
CREATE INDEX idx_document_total_incl_tax ON "document"("total_incl_tax");
