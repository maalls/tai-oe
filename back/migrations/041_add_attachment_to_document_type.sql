-- Ensure ATTACHMENT exists in document_type enum.
-- Needed for attachment document inserts in BusinessHandlers.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typname = 'document_type'
      AND e.enumlabel = 'ATTACHMENT'
  ) THEN
    ALTER TYPE public.document_type ADD VALUE 'ATTACHMENT';
  END IF;
END
$$;
