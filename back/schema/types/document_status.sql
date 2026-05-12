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
