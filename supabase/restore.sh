#!/bin/bash

# Restore script for Supabase database
# Restores latest backup in a safe order for FK dependencies

set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        -n|--dry-run)
            DRY_RUN=1
            ;;
        -h|--help)
            echo "Usage: $0 [--dry-run]"
            echo "  --dry-run, -n   Show what would be executed without changing the database"
            exit 0
            ;;
        *)
            echo "Error: unknown option '$arg'"
            echo "Usage: $0 [--dry-run]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Supabase Database Restore"
echo "=========================================="
echo ""

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "Mode: dry-run (no changes will be applied)"
    echo ""
fi

# Step 1: Drop all public tables
echo "Step 1: Dropping all public tables..."
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] docker compose --env-file .env.dev exec -T db psql -U supabase_admin -d postgres << 'EOF'"
    echo "[dry-run]   DO block ... DROP TABLE IF EXISTS public.* CASCADE ..."
    echo "[dry-run] EOF"
else
docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres << 'EOF'
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', r.tablename;
    END LOOP;
END $$;

SELECT COUNT(*) as remaining_public_tables FROM pg_tables WHERE schemaname = 'public';
EOF
fi

echo "✓ All public tables dropped"
echo ""

# Step 2: Delete auth identities and users
echo "Step 2: Deleting auth.identities and auth.users..."
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] docker compose --env-file .env.dev exec -T db psql -U supabase_admin -d postgres << 'EOF'"
    echo "[dry-run]   DELETE FROM auth.identities;"
    echo "[dry-run]   DELETE FROM auth.users;"
    echo "[dry-run] EOF"
else
docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres << 'EOF'
DELETE FROM auth.identities;
DELETE FROM auth.users;

SELECT COUNT(*) as remaining_identities FROM auth.identities;
SELECT COUNT(*) as remaining_users FROM auth.users;
EOF
fi

echo "✓ auth.identities and auth.users deleted"
echo ""

# Locate latest backup files
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_ROOT="$SCRIPT_DIR/var/backup"

if [[ ! -d "$BACKUP_ROOT" ]]; then
    echo "Error: backup root not found: $BACKUP_ROOT"
    exit 1
fi

LATEST_BACKUP_DIR="$(ls -1dt "$BACKUP_ROOT"/*/ 2>/dev/null | head -n 1 || true)"
if [[ -z "$LATEST_BACKUP_DIR" ]]; then
    echo "Error: no backup directories found in $BACKUP_ROOT"
    exit 1
fi

echo "Using backup directory: $LATEST_BACKUP_DIR"

# Step 3: Restore auth data first
echo "Step 3: Restoring auth_data from latest backup..."
AUTH_DATA_FILE="$(ls -1t "${LATEST_BACKUP_DIR}"auth_data_*.sql 2>/dev/null | head -n 1 || true)"
if [[ -z "$AUTH_DATA_FILE" ]]; then
    echo "Error: auth_data file not found in $LATEST_BACKUP_DIR"
    exit 1
fi

echo "Restoring file: $AUTH_DATA_FILE"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] docker compose --env-file .env.dev exec -T db psql -U supabase_admin -d postgres < '$AUTH_DATA_FILE'"
else
    docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres < "$AUTH_DATA_FILE"
fi

echo "✓ auth_data restored"
echo ""

# Step 4: Restore schema
echo "Step 4: Restoring schema from latest backup..."
SCHEMA_FILE="$(ls -1t "${LATEST_BACKUP_DIR}"schema_*.sql 2>/dev/null | head -n 1 || true)"
if [[ -z "$SCHEMA_FILE" ]]; then
    echo "Error: schema file not found in $LATEST_BACKUP_DIR"
    exit 1
fi

echo "Restoring file: $SCHEMA_FILE"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] docker compose --env-file .env.dev exec -T db psql -U supabase_admin -d postgres < '$SCHEMA_FILE'"
else
    docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres < "$SCHEMA_FILE"
fi

echo "✓ schema restored"
echo ""

# Step 5: Restore data with temporary FK check disable
echo "Step 5: Restoring data from latest backup (FK checks disabled)..."
DATA_FILE="$(ls -1t "${LATEST_BACKUP_DIR}"data_*.sql 2>/dev/null | head -n 1 || true)"
if [[ -z "$DATA_FILE" ]]; then
    echo "Error: data file not found in $LATEST_BACKUP_DIR"
    exit 1
fi

echo "Restoring file: $DATA_FILE"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] SET session_replication_role = replica; < '$DATA_FILE'; SET session_replication_role = origin;"
    echo "[dry-run] piped to: docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres"
else
    {
        echo "SET session_replication_role = replica;"
        cat "$DATA_FILE"
        echo "SET session_replication_role = origin;"
    } | docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres
fi

echo "✓ data restored"
echo ""

# Step 6: Post-restore sanity checks
echo "Step 6: Running post-restore sanity checks..."
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] docker compose --env-file .env.dev exec -T db psql -U supabase_admin -d postgres << 'EOF'"
    echo "[dry-run]   SELECT counts from public/auth key tables"
    echo "[dry-run] EOF"
else
docker compose --env-file .env.dev exec -T db psql -v ON_ERROR_STOP=1 -U supabase_admin -d postgres << 'EOF'
SELECT 'public table count' AS check_name, COUNT(*)::text AS value
FROM pg_tables
WHERE schemaname = 'public'
UNION ALL
SELECT 'auth.users count',
       CASE WHEN to_regclass('auth.users') IS NULL THEN 'n/a'
            ELSE (SELECT COUNT(*)::text FROM auth.users)
       END
UNION ALL
SELECT 'auth.identities count',
       CASE WHEN to_regclass('auth.identities') IS NULL THEN 'n/a'
            ELSE (SELECT COUNT(*)::text FROM auth.identities)
       END
UNION ALL
SELECT 'public.profile count',
       CASE WHEN to_regclass('public.profile') IS NULL THEN 'n/a'
            ELSE (SELECT COUNT(*)::text FROM public.profile)
       END
UNION ALL
SELECT 'public.account count',
       CASE WHEN to_regclass('public.account') IS NULL THEN 'n/a'
            ELSE (SELECT COUNT(*)::text FROM public.account)
       END;
EOF
fi

echo "✓ sanity checks completed"
echo ""
echo "Restore completed successfully."
