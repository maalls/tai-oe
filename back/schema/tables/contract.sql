-- Contract (MSA / SOW)
CREATE TABLE IF NOT EXISTS contract (
  document_id     uuid PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
  start_date      date,
  end_date        date,
  renewal_terms   text
);
