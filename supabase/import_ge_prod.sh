#!/usr/bin/env bash
set -Eeuo pipefail

# Import ge_prod dump into remote Supabase via SSH.
#
# Default behavior:
# - picks latest local backup dir matching *_ge_prod
# - creates a remote pre-restore backup
# - drops/recreates public and storage schemas on remote DB
# - imports schema_only_clean.sql then data_*.sql with session_replication_role=replica
# - runs sanity checks (including product count)
#
# Usage examples:
#   ./import_ge_prod.sh --yes
#   ./import_ge_prod.sh --backup-dir var/backup/2026-05-08_19-08-15_ge_prod --yes
#   ./import_ge_prod.sh --dry-run
#   SSH_HOST=kirin REMOTE_ENV_FILE=.env.prod ./import_ge_prod.sh --yes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="$SCRIPT_DIR/var/backup"

SSH_HOST="${SSH_HOST:-kirin}"
REMOTE_SUPABASE_DIR="${REMOTE_SUPABASE_DIR:-/home/malo/tai-oe/supabase}"
REMOTE_ENV_FILE="${REMOTE_ENV_FILE:-.env.prod}"

DB_NAME="${DB_NAME:-ge_prod}"
DB_USER="${DB_USER:-supabase_admin}"

DRY_RUN=0
ASSUME_YES=0
SKIP_PRE_BACKUP=0
BACKUP_DIR=""
EXPECT_PRODUCT_COUNT="${EXPECT_PRODUCT_COUNT:-}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --backup-dir <path>      Local backup directory to import
                           (default: latest *_${DB_NAME} in var/backup)
  --yes                    Skip destructive confirmation prompt
  --dry-run                Print actions only, do not execute
  --skip-pre-backup        Skip remote pre-restore backup creation
  --expect-product-count N Fail if remote public.product count != N
  -h, --help               Show this help

Environment overrides:
  SSH_HOST                 SSH host alias (default: kirin)
  REMOTE_SUPABASE_DIR      Remote supabase directory
  REMOTE_ENV_FILE          Remote compose env file (default: .env.prod)
  DB_NAME                  Remote database name (default: ge_prod)
  DB_USER                  Database user (default: supabase_admin)
EOF
}

for cmd in ssh docker ls grep awk; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: $cmd is required but not found in PATH." >&2
        exit 1
    fi
done

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backup-dir)
            [[ $# -ge 2 ]] || { echo "Error: --backup-dir requires a value" >&2; exit 1; }
            BACKUP_DIR="$2"
            shift 2
            ;;
        --yes)
            ASSUME_YES=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --skip-pre-backup)
            SKIP_PRE_BACKUP=1
            shift
            ;;
        --expect-product-count)
            [[ $# -ge 2 ]] || { echo "Error: --expect-product-count requires a value" >&2; exit 1; }
            EXPECT_PRODUCT_COUNT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [[ -z "$BACKUP_DIR" ]]; then
    BACKUP_DIR="$(ls -1dt "$BACKUP_ROOT"/*_"$DB_NAME"/ 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$BACKUP_DIR" ]]; then
    echo "Error: no backup directory found for pattern *_${DB_NAME} in $BACKUP_ROOT" >&2
    exit 1
fi

BACKUP_DIR="${BACKUP_DIR%/}"
if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "Error: backup directory not found: $BACKUP_DIR" >&2
    exit 1
fi

SCHEMA_CLEAN_FILE="$BACKUP_DIR/schema_only_clean.sql"
if [[ ! -f "$SCHEMA_CLEAN_FILE" ]]; then
    echo "Error: schema file not found: $SCHEMA_CLEAN_FILE" >&2
    echo "Hint: run ./export_ge_prod.sh first to generate schema_only_clean.sql" >&2
    exit 1
fi

DATA_FILE="$(ls -1 "$BACKUP_DIR"/data_*.sql 2>/dev/null | head -n 1 || true)"
if [[ -z "$DATA_FILE" || ! -f "$DATA_FILE" ]]; then
    echo "Error: data file not found in $BACKUP_DIR (expected data_*.sql)" >&2
    exit 1
fi

if [[ ! -s "$SCHEMA_CLEAN_FILE" || ! -s "$DATA_FILE" ]]; then
    echo "Error: schema or data file is empty." >&2
    exit 1
fi

if ! grep -q "COPY public.product" "$DATA_FILE"; then
    echo "Warning: COPY public.product not found in $DATA_FILE" >&2
fi

echo "Import plan:"
echo "- Source backup dir: $BACKUP_DIR"
echo "- Source schema file: $SCHEMA_CLEAN_FILE"
echo "- Source data file: $DATA_FILE"
echo "- Target SSH host: $SSH_HOST"
echo "- Target remote dir: $REMOTE_SUPABASE_DIR"
echo "- Target DB: $DB_NAME"
echo "- Target DB user: $DB_USER"
echo "- Remote env file: $REMOTE_ENV_FILE"
echo "- Remote pre-backup: $([[ "$SKIP_PRE_BACKUP" -eq 1 ]] && echo no || echo yes)"
echo "- Mode: $([[ "$DRY_RUN" -eq 1 ]] && echo dry-run || echo execute)"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo
    echo "Dry-run complete. No changes applied."
    exit 0
fi

if [[ "$ASSUME_YES" -ne 1 ]]; then
    echo
    echo "WARNING: this will DESTROY remote schemas public and storage on $SSH_HOST/$DB_NAME."
    read -r -p "Type YES to continue: " confirm
    if [[ "$confirm" != "YES" ]]; then
        echo "Aborted."
        exit 1
    fi
fi

REMOTE_PSQL_CMD="cd $REMOTE_SUPABASE_DIR && docker compose --env-file $REMOTE_ENV_FILE exec -T db psql -U $DB_USER -d $DB_NAME -v ON_ERROR_STOP=1"

# Connectivity check.
ssh "$SSH_HOST" "echo SSH_OK && hostname && whoami"

if [[ "$SKIP_PRE_BACKUP" -ne 1 ]]; then
    echo
    echo "Creating remote pre-restore backup..."
    ssh "$SSH_HOST" "cd $REMOTE_SUPABASE_DIR && TS=\$(date +'%Y-%m-%d_%H-%M-%S') && mkdir -p var/backup && docker compose --env-file $REMOTE_ENV_FILE exec -T db pg_dump -h localhost -U $DB_USER -d $DB_NAME --no-owner --no-privileges > var/backup/pre_restore_${DB_NAME}_\${TS}.sql && ls -lh var/backup/pre_restore_${DB_NAME}_\${TS}.sql"
fi

echo
echo "Resetting remote schemas public/storage..."
ssh "$SSH_HOST" "$REMOTE_PSQL_CMD" <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
DROP SCHEMA IF EXISTS storage CASCADE;
CREATE SCHEMA storage;
SQL

echo
echo "Importing schema_only_clean.sql..."
cat "$SCHEMA_CLEAN_FILE" | ssh "$SSH_HOST" "$REMOTE_PSQL_CMD"

echo
echo "Importing data with session_replication_role=replica..."
{
    echo "SET session_replication_role = replica;"
    cat "$DATA_FILE"
    echo "SET session_replication_role = origin;"
} | ssh "$SSH_HOST" "$REMOTE_PSQL_CMD"

echo
echo "Running sanity checks..."
CHECK_OUTPUT="$(ssh "$SSH_HOST" "cd $REMOTE_SUPABASE_DIR && docker compose --env-file $REMOTE_ENV_FILE exec -T db psql -U $DB_USER -d $DB_NAME -At -v ON_ERROR_STOP=1 -c \"SELECT COUNT(*) FROM public.product;\" -c \"SELECT CASE WHEN to_regclass('public.account') IS NULL THEN -1 ELSE (SELECT COUNT(*) FROM public.account) END;\" -c \"SELECT CASE WHEN to_regclass('public.opportunity') IS NULL THEN -1 ELSE (SELECT COUNT(*) FROM public.opportunity) END;\" -c \"SELECT CASE WHEN to_regclass('public.profile') IS NULL THEN -1 ELSE (SELECT COUNT(*) FROM public.profile) END;\"")"

PRODUCT_COUNT="$(echo "$CHECK_OUTPUT" | sed -n '1p')"
ACCOUNT_COUNT="$(echo "$CHECK_OUTPUT" | sed -n '2p')"
OPPORTUNITY_COUNT="$(echo "$CHECK_OUTPUT" | sed -n '3p')"
PROFILE_COUNT="$(echo "$CHECK_OUTPUT" | sed -n '4p')"

echo "- product_count: $PRODUCT_COUNT"
echo "- account_count: $ACCOUNT_COUNT"
echo "- opportunity_count: $OPPORTUNITY_COUNT"
echo "- profile_count: $PROFILE_COUNT"

if [[ -n "$EXPECT_PRODUCT_COUNT" && "$PRODUCT_COUNT" != "$EXPECT_PRODUCT_COUNT" ]]; then
    echo "Error: product_count mismatch (expected $EXPECT_PRODUCT_COUNT, got $PRODUCT_COUNT)." >&2
    exit 1
fi

echo
echo "Import completed successfully."
