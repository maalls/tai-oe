
-- ---------- OPPORTUNITY ----------

DO $$ BEGIN
  CREATE TYPE opportunity_stage AS ENUM (
    'NEW_LEAD',
    'QUALIFYING',
    'NEEDS_DEFINED',
    'RFP_IN_PROGRESS',
    'RFQ_IN_PROGRESS',
    'OFFER_SENT',
    'NEGOTIATION',
    'COMMITMENT',
    'PREPARATION',
    'DELIVERY_IN_PROGRESS',
    'ACCEPTED',
    'INVOICED',
    'PAID',
    'CLOSED_WON',
    'CLOSED_LOST',
    'ON_HOLD'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE opportunity_status AS ENUM ('OPEN', 'WON', 'LOST', 'ON_HOLD');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS opportunity (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id       uuid REFERENCES auth.users(id) ON DELETE SET NULL,
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
  changed_by     uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  changed_at     timestamptz NOT NULL DEFAULT now(),
  note           text
);

CREATE INDEX IF NOT EXISTS idx_opp_transition_opp ON opportunity_state_transition(opportunity_id, changed_at DESC);
