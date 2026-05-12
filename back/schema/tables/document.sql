-- ---------- DOCUMENT (GENERIC) ----------
CREATE TABLE IF NOT EXISTS document (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id     uuid REFERENCES opportunity(id) ON DELETE CASCADE,
  channel document_channel NOT NULL DEFAULT 'OTHER',
  source_message_id  text,
  type              document_type NOT NULL,
  status            document_status NOT NULL DEFAULT 'DRAFT',
  title             text NOT NULL,
  external_ref       text, -- ref client / ref interne
  issued_at          timestamptz,
  received_at        timestamptz,
  valid_until        date, -- mostly quote
  currency           char(3) NOT NULL DEFAULT 'EUR',
  total_excl_tax     numeric(14,2) DEFAULT 0,
  total_tax          numeric(14,2) DEFAULT 0,
  total_incl_tax     numeric(14,2) DEFAULT 0,
  storage_key        text, -- S3 key / file path
  version            integer NOT NULL DEFAULT 1 CHECK (version >= 1),
  parent_document_id uuid REFERENCES document(id) ON DELETE SET NULL,
  created_by         uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_opp ON document(opportunity_id, type);
CREATE INDEX IF NOT EXISTS idx_document_status ON document(type, status);
CREATE INDEX IF NOT EXISTS idx_document_parent ON document(parent_document_id);

CREATE INDEX IF NOT EXISTS idx_document_source_message
ON public.document (channel, source_message_id)
WHERE source_message_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_document_email_message
ON public.document (source_message_id)
WHERE channel = 'EMAIL' AND source_message_id IS NOT NULL;
