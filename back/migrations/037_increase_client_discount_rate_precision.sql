-- Migration: Increase client_discount_rate precision from NUMERIC(5,2) to NUMERIC(6,3)
-- This allows storing 3 decimal places for more accurate margin/discount calculations.
ALTER TABLE document_line
ALTER COLUMN client_discount_rate TYPE NUMERIC(6,3);
