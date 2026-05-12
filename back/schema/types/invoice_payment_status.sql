DO $$ BEGIN
  CREATE TYPE invoice_payment_status AS ENUM ('UNPAID', 'PARTIAL', 'PAID', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
