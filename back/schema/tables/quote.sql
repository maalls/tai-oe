-- Quote / Devis
CREATE TABLE IF NOT EXISTS quote (
  document_id              uuid PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
  payment_terms            text, -- e.g. "30 jours fin de mois"
  delivery_terms           text, -- delay, shipping, etc.
  incoterm                 text,
  cgv_document_id          uuid REFERENCES document(id) ON DELETE SET NULL, -- link to CGV doc if you store it as a doc
  acceptance_mode          quote_acceptance_mode,
  accepted_at              timestamptz,
  is_checked               boolean DEFAULT false,
  checked_by               uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  checked_at               timestamptz,
  verified_lines_count     integer DEFAULT 0,
  all_lines_verified       boolean DEFAULT false,
  last_verification_update timestamptz
);
