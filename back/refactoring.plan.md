# Backend Refactor Plan: RAG Handler Simplification

## Goals

- Simplify backend entrypoint and route handling.
- Eliminate regex-heavy path parsing and large conditional chains.
- Improve reliability (fewer `BrokenPipeError` cascades, cleaner error handling).
- Move to test-driven incremental refactor with zero/low functional regressions.
- Organize code by domain entrypoints (email, opportunity, quote, etc.) with clear module boundaries.

---

## Audit Summary (Current State)

### 1) Monolithic HTTP handler

- `src/controller/rag.py` is currently a monolithic request layer (~1826 lines).
- Route dispatch is scattered across large `do_GET`, `do_POST`, `do_DELETE`, `do_PUT`, `do_PATCH` methods.
- Route matching is mostly string equality (`parsed.path == ...`) and regex (`re.match(...)`) on raw URL paths.

Impact:
- High cognitive load for any feature change.
- Easy to introduce route regressions.
- Hard to validate request schemas consistently.

### 2) Regex/path parsing as control flow

- Path params are manually extracted from regex and split operations.
- Many endpoints duplicate auth checks and payload parsing branches.

Impact:
- Boilerplate repetition.
- Parsing bugs are likely (especially for edge paths/query params).
- No single source of truth for request validation.

### 3) Coupled transport + business orchestration

- `rag.py` directly handles transport concerns, auth flow decisions, parsing, and invocation orchestration.
- Some domains already exist (`controller/email`, `controller/opportunity`, `controller/quote`) but routing is not delegated cleanly.

Impact:
- Domain modules are not true entrypoints.
- Makes unit testing route behavior and orchestration difficult.

### 4) Error handling currently fragile

- Response writer can trigger nested failures (`BrokenPipeError` during JSON write then `_send_error` writes again).
- Error-to-response conversion is inconsistent across branches.

Impact:
- Noisy logs and duplicate tracebacks.
- Harder on-call troubleshooting.

### 5) Testing gaps around API contract

- Existing test suite has good domain tests in multiple areas, but API-level route contract tests are not comprehensive enough for safe large refactor.
- No strongly typed request/response contract enforcement at route boundary.

Impact:
- Refactor risk remains high without a protective endpoint-level test matrix.

---

## Recommended Architecture

## Framework and libraries

Use a well-established ASGI stack to replace manual `SimpleHTTPRequestHandler` routing:

- FastAPI for route declaration, dependency injection, and request validation.
- Pydantic v2 models for request/response schemas.
- Uvicorn as ASGI server.
- `httpx` + `pytest` + `pytest-asyncio`/sync TestClient for endpoint contract tests.

Why this stack:
- Removes manual regex path parsing via typed path parameters.
- Centralized validation and clean 4xx/5xx behavior.
- Built-in docs and route discoverability.
- Easier modular routers per domain.

---

## Target Folder Structure

Proposed new API entrypoint under `src/api` while preserving existing domain logic in `src/controller`/`src/repository` during migration:

```text
src/
	api/
		app.py
		deps.py
		error_handlers.py
		routers/
			health.py
			auth.py
			email.py
			opportunity.py
			quote.py
			product.py
			filesystem.py
			qdrant.py
			actions.py
	services/
		opportunity_service.py
		quote_service.py
		email_service.py
	schemas/
		common.py
		opportunity.py
		quote.py
		email.py
```

Notes:
- Keep existing modules as adapters first, then progressively extract service layer.
- Route modules should be thin: validate input -> call service -> return typed response.

---

## Refactor Strategy (TDD-First, Incremental)

## Phase 0: Freeze behavior with contract tests

Create endpoint contract tests before replacing routing.

Priority tests:
- Authentication required vs optional routes.
- Opportunity creation/search/delete endpoints.
- Quote generation endpoints (including RFQ/RFP flows).
- Email auth/resync/delete paths.
- Error shape consistency (`status`, `message`, HTTP code).

Artifacts:
- `tests/integration/api_contract/test_*.py`
- Golden request/response fixtures for critical endpoints.

Exit criteria:
- Current behavior captured and reproducible.

## Phase 1: Introduce new API app in parallel

- Add `src/api/app.py` with FastAPI app and a health router.
- Keep current `src/controller/rag.py` running as primary until parity is proven.
- Add a feature flag/env switch:
	- `API_IMPL=legacy|fastapi`

Exit criteria:
- New app boots locally and serves `/health`.

## Phase 2: Migrate routes domain by domain

Order (risk-managed):
1. Read-only/simple routes (`/api/opportunities/search`, status endpoints).
2. CRUD endpoints with auth.
3. Complex generation routes (RFQ/RFP/quote).
4. Optional integrations (Qdrant-dependent routes).

For each migrated endpoint:
- Add/adjust Pydantic schemas.
- Add integration tests for success + validation + auth + failure paths.
- Keep old handler route until endpoint parity is validated.

Exit criteria:
- Endpoint family green in CI against contract tests.

## Phase 3: Centralize dependencies and feature flags

- Consolidate env parsing in one config module (`pydantic-settings` recommended).
- Move toggles like `ENABLE_QDRANT` into typed settings.
- Inject dependencies via FastAPI `Depends` instead of class-level singletons.

Exit criteria:
- No direct env lookups scattered in route handlers.

## Phase 4: Remove legacy routing and cleanup

- Deprecate `src/controller/rag.py` dispatch logic.
- Keep a minimal compatibility wrapper only if needed for startup.
- Update `dev.py` to start Uvicorn app module.

Exit criteria:
- Legacy route chain removed; all API traffic served by modular routers.

---

## Routing and Validation Guidelines

- No raw regex route parsing in transport layer.
- Use typed path params (`/api/opportunity/{opportunity_id}` with UUID type where relevant).
- Validate query/body via schemas, not ad-hoc dict reads.
- Standardize response envelope for errors and business failures.
- Add exception handlers for:
	- validation errors,
	- domain errors,
	- uncaught exceptions.

---

## Test-Driven Plan Details

## Test pyramid

- Unit tests:
	- pure service logic,
	- parser/mapper helpers,
	- policy decisions (auth checks, feature flags).
- Integration tests:
	- FastAPI TestClient route tests,
	- mocked repositories/external dependencies.
- Select end-to-end tests:
	- quote generation happy path,
	- RFQ import flow,
	- auth-protected CRUD flow.

## Minimum coverage gate for migration

- 80%+ for newly introduced API modules.
- 100% coverage on high-risk route branches (auth, error mapping, feature flags).

## Regression focus

- Ensure no reappearance of double `/api/api` route assembly.
- Ensure no duplicate write attempts after client disconnect (`BrokenPipeError` handling).
- Ensure `ENABLE_QDRANT=false` is honored at all API entrypoints.

---

## Immediate Refactor Backlog (Recommended Next PRs)

1. Create FastAPI scaffold (`src/api/app.py`, `routers/health.py`, `settings.py`).
2. Add contract tests for current opportunity search/create/delete endpoints.
3. Migrate opportunity routes first (high value, medium complexity).
4. Add global exception handlers and a unified error response model.
5. Migrate RFQ/RFP quote endpoints with explicit request models.
6. Migrate email routes and remove manual path splitting.
7. Switch runtime entrypoint in `dev.py` to FastAPI app.

---

## Risks and Mitigations

- Risk: behavior drift during migration.
	- Mitigation: contract tests before endpoint migration.

- Risk: mixed architecture during transition creates confusion.
	- Mitigation: explicit `API_IMPL` switch and migration checklist per endpoint group.

- Risk: dependency wiring bugs after singleton removal.
	- Mitigation: centralized settings/deps module + focused dependency injection tests.

---

## Definition of Done

- All legacy regex/path-based route dispatch in `rag.py` removed or bypassed.
- API endpoints served from modular routers grouped by domain.
- Typed schemas for all non-trivial request/response contracts.
- Contract tests and integration tests green in CI.
- Operational docs updated (run/dev/deploy, feature flags, troubleshooting).

