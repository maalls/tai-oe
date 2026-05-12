ALTER TABLE family
  DROP CONSTRAINT IF EXISTS family_document_id_fkey;

DROP INDEX IF EXISTS idx_family_document;

ALTER TABLE family
  DROP COLUMN IF EXISTS document_id;
