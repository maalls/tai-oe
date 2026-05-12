CREATE TABLE IF NOT EXISTS contact (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id  uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
  name        text NOT NULL,
  email       text,
  phone       text,
  role_title  text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contact_account ON contact(account_id);
CREATE INDEX IF NOT EXISTS idx_contact_email ON contact(email);
