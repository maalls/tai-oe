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
    'FAMILY_DISCOUNT',
    'ATTACHMENT'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
