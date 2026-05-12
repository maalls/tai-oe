ALTER TABLE family
  ADD COLUMN IF NOT EXISTS document_id uuid;

ALTER TABLE family
  ALTER COLUMN document_id SET NOT NULL;

ALTER TABLE family
  ADD CONSTRAINT family_document_id_fkey
  FOREIGN KEY (document_id) REFERENCES document(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_family_document ON family (document_id);
