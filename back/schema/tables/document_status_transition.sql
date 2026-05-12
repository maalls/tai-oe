-- Document status transitions (optional)
CREATE TABLE IF NOT EXISTS document_status_transition (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id  uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  from_status  document_status,
  to_status    document_status NOT NULL,
  changed_by   uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  changed_at   timestamptz NOT NULL DEFAULT now(),
  note         text
);

CREATE INDEX IF NOT EXISTS idx_doc_transition_doc ON document_status_transition(document_id, changed_at DESC);
