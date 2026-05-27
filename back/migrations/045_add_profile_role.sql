-- Add role to profile for basic RBAC (admin/user)
ALTER TABLE profile
ADD COLUMN IF NOT EXISTS role text;

UPDATE profile
SET role = 'user'
WHERE role IS NULL OR btrim(role) = '';

ALTER TABLE profile
ALTER COLUMN role SET DEFAULT 'user';

ALTER TABLE profile
ALTER COLUMN role SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'profile_role_check'
    ) THEN
        ALTER TABLE profile
        ADD CONSTRAINT profile_role_check
        CHECK (role IN ('admin', 'user'));
    END IF;
END $$;
