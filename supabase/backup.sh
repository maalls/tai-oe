#!/usr/bin/env bash
set -Eeuo pipefail

# Usage examples:
#   TARGET_ENV=dev ./backup.sh
#   ./backup.sh (defaults to prod)

for cmd in docker; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		echo "Error: $cmd is required but not found in PATH." >&2
		exit 1
	fi
done

TARGET_ENV="${TARGET_ENV:-prod}"
if [[ "$TARGET_ENV" != "dev" && "$TARGET_ENV" != "prod" ]]; then
	echo "Error: TARGET_ENV must be 'dev' or 'prod' (got '$TARGET_ENV')." >&2
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.$TARGET_ENV"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
BACKUP_DIR="$SCRIPT_DIR/var/backup/$TIMESTAMP"

if [[ ! -f "$ENV_FILE" ]]; then
	echo "Error: env file not found: $ENV_FILE" >&2
	exit 1
fi

mkdir -p "$BACKUP_DIR"

SCHEMA_ARGS=(--schema public --schema storage)
COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$SCRIPT_DIR/docker-compose.yml")

echo "Backup source: docker compose db ($TARGET_ENV)"
echo "Compose dir: $SCRIPT_DIR"
echo "Schemas: public, storage"
echo "Auth tables: auth.users, auth.identities"
echo "Output: $BACKUP_DIR"

"${COMPOSE[@]}" ps db >/dev/null

# Schema dump
"${COMPOSE[@]}" exec -T db pg_dump -h localhost -U supabase_admin -d postgres \
	--no-owner --no-privileges "${SCHEMA_ARGS[@]}" > "$BACKUP_DIR/schema_$TIMESTAMP.sql"

# Data dump
"${COMPOSE[@]}" exec -T db pg_dump -h localhost -U supabase_admin -d postgres \
	--no-owner --no-privileges --data-only --use-set-session-authorization "${SCHEMA_ARGS[@]}" > "$BACKUP_DIR/data_$TIMESTAMP.sql"

# Auth users dump (needed by public FKs such as profile.id -> auth.users.id)
"${COMPOSE[@]}" exec -T db pg_dump -h localhost -U supabase_admin -d postgres \
	--no-owner --no-privileges --data-only --use-set-session-authorization \
	--table=auth.users --table=auth.identities > "$BACKUP_DIR/auth_data_$TIMESTAMP.sql"

# Roles dump
"${COMPOSE[@]}" exec -T db pg_dumpall -h localhost -U supabase_admin --roles-only > "$BACKUP_DIR/roles_$TIMESTAMP.sql"

# Verify all backup files exist and are not empty
if [[ $(find "$BACKUP_DIR" -name "*.sql" -type f -size +0) == "" ]]; then
	echo "Error: backup files are empty or missing." >&2
	exit 1
fi

echo "Backup completed: $BACKUP_DIR"
echo "File sizes:"
ls -lh "$BACKUP_DIR"/*.sql
