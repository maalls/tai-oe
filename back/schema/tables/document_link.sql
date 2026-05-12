-- Links between docs (quote->po->invoice etc.)
CREATE TABLE IF NOT EXISTS document_link (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  from_document_id  uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  to_document_id    uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  link_type         document_link_type NOT NULL,
  is_ref_verified boolean DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (from_document_id, to_document_id, link_type)
);

CREATE INDEX IF NOT EXISTS idx_doc_link_from ON document_link(from_document_id);
CREATE INDEX IF NOT EXISTS idx_doc_link_to ON document_link(to_document_id);
