# DB Config Refactoring Plan (Single Source via SUPABASE_ENV_FILE)

## Goal

Create a single, reliable configuration source for database and Supabase credentials by deriving runtime config from `SUPABASE_ENV_FILE`, then exposing profile-specific connection settings through a dedicated infrastructure factory.

This plan targets:

- one source of truth for secrets and DB host/db metadata
- explicit profile derivation (`app`, `migration`, optional `readonly`)
- no ad-hoc config parsing spread across commands/services
- gradual migration with safety checks and reversible commits

## Scope

In scope:

- backend config loading and normalization
- DB profile factory + connection service
- migration scripts/CLIs using shared factory
- supabase client env resolution alignment
- tests for config derivation and profile correctness

Out of scope:

- rotating production secrets
- changing DB schema/model behavior
- frontend env flow

## Architectural Target

### Current pain points

- config resolution is duplicated (`env_loader`, `supabase.py`, `database.py`, migration scripts)
- import-time env mutation causes hidden ordering behavior
- migration/admin profile derivation is custom and local to script
- `DATABASE_URL` is overloaded for both runtime and schema migration concerns

### Target design

1. `ConfigProvider` (single source reader)

- loads process env + local `.env` + shared `SUPABASE_ENV_FILE`
- validates required keys
- returns typed immutable config object

2. `DbProfileFactory` (derived views)

- derives explicit DB profiles:
  - `app` profile: runtime usage
  - `migration` profile: schema migration/admin usage
  - `service` profile (optional)
- handles tenant suffix mapping (e.g. `*.ge-prod`) consistently

3. `DatabaseService` (connection boundary)

- opens psycopg2 connections from a selected profile
- centralizes connect options (sslmode, timeout, db name override)
- used by commands and migration scripts

4. `SupabaseConfigAdapter`

- resolves URL/keys from the same typed config object
- avoids import-time side effects and duplicated dotenv loading

## Non-Functional Requirements

- deterministic behavior across all entrypoints (`python -m ...`, tests, services)
- no secrets duplicated in backend `.env` when `SUPABASE_ENV_FILE` is present
- clear error messages for missing/invalid config
- test coverage for all profile derivation branches

## Delivery Strategy

Incremental, test-first migration in 8 phases with micro-commits.

---

## Phase 0 - Baseline and Safety Net

### Steps

1. Freeze baseline behavior with characterization tests.
2. Capture current env precedence rules (document expected behavior).
3. Add temporary observability logs (masked) for profile source selection.

### TDD checklist

- [x] Add failing characterization tests for current config resolution paths.
- [x] Make tests pass without refactor.
- [x] Confirm no regressions in existing migration tests.

### Commit reminder

Commit once phase is green:

- `test(config): add characterization tests for current env resolution`

---

## Phase 1 - Introduce Typed Config Model

### Steps

1. Add typed config dataclasses:

- `SharedSupabaseConfig`
- `DatabaseRuntimeHints`
- `ResolvedRuntimeConfig`

2. Add parser utilities:

- normalize booleans, ints, URLs, optional keys
- strict validation with actionable exceptions

3. Add masking helpers for safe logging.

### TDD checklist

- [x] Write parser tests first (missing key, malformed URL, valid file).
- [x] Implement model and parser to satisfy tests.
- [x] Add tests for masking utility.

### Commit reminder

- `feat(config): add typed runtime config models and parser`

---

## Phase 2 - Build ConfigProvider (Single Source)

### Steps

1. Create infrastructure module (example):

- `src/infrastructure/config/provider.py`

2. Implement precedence:

- explicit process env override
- local `.env` fallback
- shared file from `SUPABASE_ENV_FILE`

3. Provide one entrypoint API:

- `get_runtime_config()`

4. Remove direct `dotenv_values` use from consumers progressively.

### TDD checklist

- [x] Write tests for precedence order.
- [x] Write tests for relative/absolute `SUPABASE_ENV_FILE` resolution.
- [x] Write tests for missing shared file behavior.
- [x] Implement provider until tests pass.

### Commit reminder

- `feat(config): add ConfigProvider with SUPABASE_ENV_FILE precedence`

---

## Phase 3 - Build DbProfileFactory

### Steps

1. Add `DbProfile` model:

- host, port, user, password, database, sslmode, source

2. Implement profile derivation methods:

- `build_app_profile(config)`
- `build_migration_profile(config)`

3. Add tenant-aware username logic:

- derive suffix from app user when required
- map to `supabase_admin[.tenant]` for migration profile

4. Add validation helpers:

- profile completeness
- unsupported combination detection

### TDD checklist

- [x] Start with failing tests for tenant/no-tenant username derivation.
- [x] Add tests for migration profile fallback chain.
- [x] Add tests for malformed or missing password in shared env.
- [x] Implement factory until tests pass.

### Commit reminder

- `feat(db): add DbProfileFactory for app and migration profiles`

---

## Phase 4 - Build DatabaseService / Connection Factory

### Steps

1. Add `DatabaseService` API:

- `connect(profile_name="app")`
- `cursor(profile_name="app")`

2. Centralize psycopg2 connect wiring.
3. Keep log output masked and explicit about selected profile source.

### TDD checklist

- [x] Add unit tests with mocked psycopg2 connect args.
- [x] Add integration-like tests for profile name selection.
- [x] Ensure failure messages include remediation guidance.

### Commit reminder

- `feat(db): add DatabaseService connection factory`

---

## Phase 5 - Migrate Existing Consumers

### Steps

1. Refactor `src/infrastructure/clients/database.py` to consume `DatabaseService`/`DbProfileFactory`.
2. Refactor `src/infrastructure/clients/supabase.py` to use `ConfigProvider` (remove duplicate dotenv side effects).
3. Refactor migration scripts/CLIs:

- `script/run_migrations.py`
- `src/command/migrations_cli.py`
- `src/command/run_migration.py`

4. Remove duplicated parsing logic from each consumer.

### TDD checklist

- [x] Add/adjust unit tests per consumer before refactor.
- [x] Update tests to assert same behavior with new provider.
- [x] Verify migration execution path in tests uses derived migration profile.

### Commit reminder

Use micro-commits, one per consumer:

- `refactor(db): move database.py to DatabaseService`
- `refactor(config): make supabase client use ConfigProvider`
- `refactor(migration): unify migration DB profile resolution`

---

## Phase 6 - Cleanup and Dead Code Removal

### Steps

1. Remove obsolete helper functions and duplicated env-loading logic.
2. Remove conflicting precedence docs/comments in old modules.
3. Ensure only one official config-loading path remains.
4. Consolidate parallel migration entrypoints to a canonical flow (or make legacy commands delegates).
5. Align `src/infrastructure/runtime/env_loader.py` with `ConfigProvider` to avoid dual env mutation systems.
6. Reduce/remove singleton DB wiring (`get_db_handler`) when it conflicts with explicit injection.

### TDD checklist

- [x] Run full backend tests.
- [x] Add regression tests that fail if legacy loaders are accidentally reintroduced.

### Commit reminder

- `chore(config): remove legacy env-loading paths and dead code`

---

## Phase 7 - Docs and Runbook

### Steps

1. Update backend docs with new architecture and precedence.
2. Add quick recipes:

- local dev using `SUPABASE_ENV_FILE`
- explicit override with `MIGRATION_DATABASE_URL`
- troubleshooting matrix for common errors

3. Add security note:

- no plaintext secrets in committed files for non-dev environments.

### TDD checklist

- [x] Validate documented commands against real local setup.
- [x] Ensure docs reflect actual tested behavior.

### Commit reminder

- `docs(db): document single-source config and profile factory usage`

---

## Phase 8 - Hardening and Final Validation

### Steps

1. Run complete test suite and targeted integration checks.
2. Run migration dry-run and actual run on local stack.
3. Validate app runtime path still works with same env setup.
4. Verify no direct secret duplication needed in `back/.env`.

### TDD checklist

- [x] Add one end-to-end test for migration profile resolution from shared env.
- [x] Add one end-to-end test for app profile resolution.

### Commit reminder

- `test(e2e): validate unified db config resolution`
- `release: finalize db config refactor`

---

## Master TODO List

- [x] Baseline characterization tests added and passing.
- [x] Typed config models implemented.
- [x] ConfigProvider implemented with precedence tests.
- [x] DbProfileFactory implemented with tenant-aware tests.
- [x] DatabaseService connection factory implemented.
- [x] `database.py` migrated to shared factory.
- [x] `supabase.py` migrated to shared provider.
- [x] all migration command paths migrated.
- [x] duplicate env loaders removed.
- [x] dependency inversion completed for database client/repository boundaries.
- [x] legacy singleton DB wiring reduced or removed.
- [x] docs/runbook updated.
- [x] full test suite green.
- [x] end-to-end migration validation complete.

## Progress Snapshot

- [x] Phase 0 completed.
- [x] Phase 1 completed.
- [x] Phase 2 completed.
- [x] Phase 3 completed.
- [x] Phase 4 completed.
- [x] Phase 5 completed.
- [x] Phase 6 completed.
- [x] Phase 7 completed.
- [x] Phase 8 completed.

Phase 5 completed items:

- [x] `src/infrastructure/clients/supabase.py` migrated to `ConfigProvider`.
- [x] `script/run_migrations.py` migrated to bootstrap + `DatabaseService` orchestration.
- [x] `src/infrastructure/clients/database.py` now routes app connection through `DatabaseService`.
- [x] `src/command/migrations_cli.py` delegates to `script.run_migrations` as canonical entrypoint.
- [x] `src/command/run_migration.py` delegates to `script.run_migrations` as canonical entrypoint.
- [x] API routers now consume `get_database_repository` dependency injection instead of local DB constructors.

Phase 6 ongoing cleanup notes:

- [x] Replaced legacy `load_dotenv` entrypoint loading in `src/command/*` with `load_runtime_env` bootstrap.
- [x] Added regression guard test to detect legacy dotenv usage in command entrypoints.
- [x] Migrated `script/db_create.py` from `DATABASE_URL`/`load_dotenv` to migration profile resolution via unified config service.

Recent implementation commits:

- `84b12db` test(config): characterization tests baseline
- `4789f64` feat(config): typed config models + parser
- `c7b4982` feat(config): ConfigProvider
- `7059614` feat(db): DbProfileFactory
- `45003ef` feat(db): DatabaseService
- `c71d84d` refactor(config): supabase client -> ConfigProvider
- `9f4545b` refactor(migration): run_migrations profile resolution
- `4d11fb4` refactor(db): move migration source resolution to factory/service
- `5bf64b2` refactor(db): script orchestration-only via service bootstrap
- `32bd616` refactor(db): DatabaseHandler connections via DatabaseService
- `3b914f1` refactor(db): enforce shared env DB source and central DI wiring
- `a02f73c` test(api): switch overrides to centralized db dependency
- `65883ce` chore(config): remove legacy dotenv loaders in command entrypoints
- `22a3d8a` refactor(db): migrate db_create to unified migration profile
- `0c0f1cd` refactor(config): split bootstrap composition helpers
- `27aeaec` refactor(config): reuse bootstrap runtime resolver in clients

## Quality Gates (Do Not Skip)

For every phase:

1. Write/adjust tests first (TDD).
2. Make the smallest code change to pass tests.
3. Run targeted tests + impacted integration tests.
4. Commit immediately with an atomic message.

## Commit Discipline (Reminder)

- One logical change per commit.
- No mixed refactor + behavior change without tests.
- Commit message format:
  - `feat(...)`
  - `refactor(...)`
  - `test(...)`
  - `docs(...)`
  - `chore(...)`

Recommended sequence:

1. tests
2. implementation
3. cleanup
4. docs

## Risks and Mitigations

- Risk: hidden runtime differences due to import order.
  - Mitigation: eliminate import-time env mutation, centralize provider call.

- Risk: tenant suffix edge cases break migration auth.
  - Mitigation: explicit unit tests for tenant/no-tenant variants.

- Risk: accidental fallback to low-privilege app profile in migrations.
  - Mitigation: explicit migration profile selection and fail-fast privilege checks.

- Risk: secrets copied between files.
  - Mitigation: derive from shared env source and document no-duplication policy.

## Definition of Done

- All DB/Supabase config consumers use the same provider/factory pipeline.
- Migrations succeed using derived admin profile from `SUPABASE_ENV_FILE` without local secret duplication.
- Runtime app connections continue to work unchanged.
- No duplicated config loaders remain.
- Tests are green and updated.
- Documentation and runbook reflect final behavior.
