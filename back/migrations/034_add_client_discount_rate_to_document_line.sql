-- Migration: Add client_discount_rate to document_line
ALTER TABLE document_line
ADD COLUMN client_discount_rate NUMERIC(6,3);
