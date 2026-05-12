#!/usr/bin/env bash
set -Eeuo pipefail

# Export ge_prod in a restore-friendly format:
# - schema-only for public/storage
# - clean schema file without CREATE SCHEMA public/storage lines
# - data-only for public/storage
#
# Usage examples:
#   ./export_ge_prod.sh
#   ENV_FILE=/path/to/.env.prod ./export_ge_prod.sh
#   DB_NAME=ge_prod OUT_DIR=var/backup/custom_export ./export_ge_prod.sh

for cmd in docker awk grep; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		echo "Error: $cmd is required but not found in PATH." >&2
		exit 1
	fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"
DB_NAME="${DB_NAME:-ge_prod}"
DB_USER="${DB_USER:-supabase_admin}"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/var/backup/${TIMESTAMP}_${DB_NAME}}"

SCHEMA_FILE="$OUT_DIR/schema_only_${TIMESTAMP}_${DB_NAME}.sql"
CLEAN_SCHEMA_FILE="$OUT_DIR/schema_only_clean.sql"
DATA_FILE="$OUT_DIR/data_${TIMESTAMP}.sql"

if [[ ! -f "$ENV_FILE" ]]; then
	echo "Error: env file not found: $ENV_FILE" >&2
	echo "Hint: set ENV_FILE explicitly, e.g. ENV_FILE=$SCRIPT_DIR/.env.prod" >&2
	exit 1
fi

mkdir -p "$OUT_DIR"

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$SCRIPT_DIR/docker-compose.yml")
SCHEMA_ARGS=(--schema public --schema storage)

# Fail early if db service is unavailable.
"${COMPOSE[@]}" ps db >/dev/null

echo "Export source: db=$DB_NAME user=$DB_USER"
echo "Env file: $ENV_FILE"
echo "Output dir: $OUT_DIR"

"${COMPOSE[@]}" exec -T db pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" \
	--no-owner --no-privileges --schema-only "${SCHEMA_ARGS[@]}" > "$SCHEMA_FILE"

awk '
	/^CREATE SCHEMA public;$/ { next }
	/^CREATE SCHEMA storage;$/ { next }
	/^COMMENT ON SCHEMA public IS / { next }
	{ print }
' "$SCHEMA_FILE" > "$CLEAN_SCHEMA_FILE"

"${COMPOSE[@]}" exec -T db pg_dump -h localhost -U "$DB_USER" -d "$DB_NAME" \
	--no-owner --no-privileges --data-only --use-set-session-authorization "${SCHEMA_ARGS[@]}" > "$DATA_FILE"

if [[ ! -s "$SCHEMA_FILE" || ! -s "$CLEAN_SCHEMA_FILE" || ! -s "$DATA_FILE" ]]; then
	echo "Error: one or more export files are empty." >&2
	exit 1
fi

echo "Export completed."
ls -lh "$SCHEMA_FILE" "$CLEAN_SCHEMA_FILE" "$DATA_FILE"

if grep -q "COPY public.product" "$DATA_FILE"; then
	echo "Check: found COPY public.product in data file."
else
	echo "Warning: COPY public.product not found in data file."
fi

HAS_PRODUCT_TABLE="$(${COMPOSE[@]} exec -T db psql -U "$DB_USER" -d "$DB_NAME" -Atqc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='product');")"
if [[ "$HAS_PRODUCT_TABLE" == "t" ]]; then
	PRODUCT_COUNT="$(${COMPOSE[@]} exec -T db psql -U "$DB_USER" -d "$DB_NAME" -Atqc "SELECT COUNT(*) FROM public.product;")"
	echo "Check: public.product count = $PRODUCT_COUNT"
fi

echo
echo "Restore reminder (target remote ge_prod):"
echo "1) Reset schemas public/storage"
echo "2) Import schema_only_clean.sql"
echo "3) Import data with session_replication_role=replica"
