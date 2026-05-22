# DB Config Runbook (Single Source)

## Architecture

The backend now resolves DB and Supabase settings through a single pipeline:

1. `SUPABASE_ENV_FILE` provides shared credentials and DB host metadata.
2. `ConfigProvider` normalizes values into `ResolvedRuntimeConfig`.
3. `DbProfileFactory` derives explicit connection profiles (`app`, `migration`).
4. `DatabaseService` is the only connection boundary used by commands/services.

`DATABASE_URL`, `ADMIN_DATABASE_URL`, and `MIGRATION_DATABASE_URL` are intentionally ignored for profile derivation.

## Environment Precedence

1. Process environment variables
2. Local `.env` values (if present)
3. Shared file pointed by `SUPABASE_ENV_FILE` (default fallback path if unset)

For database profile values, shared env keys are authoritative (`POSTGRES_*`).

## Local Setup Recipe

1. Create shared env file (example: `supabase/.env.prod`) with:
   - `POSTGRES_PASSWORD`
   - `POSTGRES_USER`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`
   - `POSTGRES_DB`
   - `SUPABASE_PUBLIC_URL` / `ANON_KEY` / `SERVICE_ROLE_KEY` as needed
2. Point backend to shared file:

```bash
export SUPABASE_ENV_FILE=../supabase/.env.prod
```

3. Run backend tests:

```bash
cd back
venv/bin/pytest
```

## Migration Recipe (Canonical Entry)

Use one migration entrypoint:

```bash
cd back
venv/bin/python -m script.run_migrations
```

Compatibility command (kept for old automation):

```bash
cd back
venv/bin/python -m src.command.migrations_cli --reset
```

## Troubleshooting Matrix

- Error: `Missing required key POSTGRES_PASSWORD in shared Supabase env`
  - Check `SUPABASE_ENV_FILE` path and file content.
  - Ensure `POSTGRES_PASSWORD` exists in the shared file.

- Error: migration role missing `CREATE` on schema `public`
  - Grant `CREATE` privilege for the configured role in shared env.

- Error: Supabase URL/key missing
  - Verify `SUPABASE_PUBLIC_URL` / `ANON_KEY` / `SERVICE_ROLE_KEY` in shared env.

## Security Notes

- Do not commit real secrets to repository files.
- Keep production secrets only in secure environment stores.
- Avoid duplicating secrets in both `back/.env` and `SUPABASE_ENV_FILE`.

## Verified Commands (this workspace)

The following commands were validated in this workspace:

```bash
cd back
venv/bin/python -m src.command.migrations_cli --help
venv/bin/python -m src.command.email_cli --help
venv/bin/pytest tests/integration/infrastructure/config/bootstrap/test_create_database_service_profile_resolution.py
venv/bin/pytest
```
