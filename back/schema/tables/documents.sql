-- =========================
-- CRM / Sales (France/UE) - PostgreSQL schema
-- =========================
-- Notes:
-- - Uses enums for stages/status
-- - Generic "document" table + specialized tables (quote, purchase_order, contract, invoice)
-- - Versioning via parent_document_id + version
-- - Links between documents via document_link
-- - Line items in document_line (RFQ/Quote/PO/Invoice share same structure)

BEGIN;

-- ---------- ENUMS ----------

DO $$ BEGIN
  CREATE TYPE document_type AS ENUM (
    'RFI',
    'RFP',
    'RFQ',
    'PROPOSAL',
    'QUOTE',
    'PO',
    'CONTRACT',
    'DELIVERY_NOTE',
    'ACCEPTANCE',
    'INVOICE',
    'CREDIT_NOTE',
    'NDA',
    'DPA',
    'SLA',
    'CGV',
    'FAMILY_DISCOUNT'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Generic doc status (some statuses apply only to some types)
DO $$ BEGIN
  CREATE TYPE document_status AS ENUM (
    'DRAFT',
    'SENT',
    'RECEIVED',
    'SUBMITTED',
    'SHORTLISTED',
    'ACCEPTED',
    'REJECTED',
    'CONFIRMED',
    'FULFILLED',
    'CANCELLED',
    'EXPIRED',
    'PAID',
    'PARTIALLY_PAID',
    'OVERDUE',
    'DISPUTED',
    'APPLIED'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$
BEGIN
  CREATE TYPE document_channel AS ENUM (
    'EMAIL',
    'PORTAL',
    'PHONE',
    'MANUAL',
    'OTHER'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END
$$;

DO $$ BEGIN
  CREATE TYPE contact_role AS ENUM ('DECISION_MAKER', 'INFLUENCER', 'BUYER', 'TECHNICAL', 'FINANCE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE document_link_type AS ENUM (
    'QUOTE_TO_PO',
    'PO_TO_INVOICE',
    'QUOTE_TO_INVOICE',
    'CONTRACT_TO_SOW',
    'DELIVERY_TO_INVOICE',
    'ACCEPTANCE_TO_INVOICE',
    'QUOTE_REVISION'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE invoice_payment_status AS ENUM ('UNPAID', 'PARTIAL', 'PAID', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE quote_acceptance_mode AS ENUM ('SIGNED_QUOTE', 'EMAIL_OK', 'PORTAL_CLICK');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE unit_type AS ENUM ('U', 'M', 'H', 'DAY', 'PACK', 'KG', 'L');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------- EXTENSIONS ----------
-- For UUID generation (choose one strategy)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------- CORE TABLES ----------



CREATE TABLE IF NOT EXISTS profile (
  id          uuid NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT PRIMARY KEY,
  email       text UNIQUE,
  full_name   text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------- OPPORTUNITY ----------
CREATE TABLE IF NOT EXISTS opportunity (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id       uuid REFERENCES user(id) ON DELETE SET NULL,
  account_id          uuid NOT NULL REFERENCES account(id) ON DELETE RESTRICT,
  name                text NOT NULL,
  stage               opportunity_stage NOT NULL DEFAULT 'NEW_LEAD',
  status              opportunity_status NOT NULL DEFAULT 'OPEN',
  currency            char(3) NOT NULL DEFAULT 'EUR',
  amount_estimated    numeric(14,2) DEFAULT 0,
  probability         integer NOT NULL DEFAULT 10 CHECK (probability >= 0 AND probability <= 100),
  expected_close_date date,
  
  source              text, -- inbound/outbound/partner...
  source_reference_id uuid, -- e.g. email.id, meeting.id, call.id depending on source
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_opportunity_account ON opportunity(account_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_stage_status ON opportunity(stage, status);
CREATE INDEX IF NOT EXISTS idx_opportunity_close_date ON opportunity(expected_close_date);
-- Create index for efficient lookups by source type and reference
CREATE INDEX IF NOT EXISTS idx_opportunity_source_ref 
ON opportunity(source, source_reference_id) 
WHERE source_reference_id IS NOT NULL;

ALTER TABLE opportunity
ADD CONSTRAINT check_stage_status_consistency CHECK (
  (
    -- CLOSED_WON must have WON status
    (stage = 'CLOSED_WON' AND status = 'WON')
    OR
    -- CLOSED_LOST must have LOST status
    (stage = 'CLOSED_LOST' AND status = 'LOST')
    OR
    -- All other stages cannot have WON or LOST status
    (stage NOT IN ('CLOSED_WON', 'CLOSED_LOST') AND status NOT IN ('WON', 'LOST'))
  )
);

CREATE TABLE IF NOT EXISTS opportunity_participant (
  opportunity_id  uuid NOT NULL REFERENCES opportunity(id) ON DELETE CASCADE,
  contact_id      uuid NOT NULL REFERENCES contact(id) ON DELETE CASCADE,
  role            contact_role NOT NULL,
  PRIMARY KEY (opportunity_id, contact_id)
);

-- Transition history (optional but recommended)
CREATE TABLE IF NOT EXISTS opportunity_state_transition (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id uuid NOT NULL REFERENCES opportunity(id) ON DELETE CASCADE,
  from_stage     opportunity_stage,
  to_stage       opportunity_stage NOT NULL,
  changed_by     uuid REFERENCES user(id) ON DELETE SET NULL,
  changed_at     timestamptz NOT NULL DEFAULT now(),
  note           text
);

CREATE INDEX IF NOT EXISTS idx_opp_transition_opp ON opportunity_state_transition(opportunity_id, changed_at DESC);

-- Document-related tables were moved to dedicated schema files.

COMMIT;
