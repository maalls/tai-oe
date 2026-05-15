# Phase 4 Reorganization Plan (Code + API + Cleanup)

## 1. Scope and Goal

This plan reorganizes backend code into clear layers and reduces complexity by removing dead or obsolete code.

Target layers:

- `domain`: pure business models and rules
- `repository`: data access contracts and persistence interfaces
- `infrastructure`: concrete technical implementations (Supabase, external clients, filesystem)
- `service`: business orchestration and workflows
- `api`: HTTP adapters/routes/controllers (request parsing + response mapping only)

## 2. Clear End Condition (Definition of Done)

Phase 4 is complete when all conditions are true:

1. Backend modules are mapped and moved into one of the 5 layers above.
2. `api` contains HTTP concerns only (no heavy business logic).
3. Controller monolith (`back/src/controller/rag.py`) is reduced to routing/compatibility glue or fully split.
4. Legacy wrappers are explicitly listed and minimized.
5. Dead/unused functions identified in the cleanup register are removed (or justified and kept).
6. Unit tests mirror runtime folders for migrated modules.
7. Regression suites are green after each micro-step:
   - command tests
   - controller/api tests
   - domain/service/repository tests for touched modules
8. Plan status files are updated to mark Phase 4 done.

## 3. Delivery Strategy (Start -> Finish)

### Phase A: Inventory and Classification (Start)

- Build a module inventory of `back/src`:
  - source path
  - target layer
  - keep/move/delete decision
  - migration priority
- Build endpoint inventory from current HTTP entrypoints:
  - endpoint
  - current handler
  - target service
  - target `api` module

Exit criteria:

- Inventory and endpoint map completed and reviewed.

### Phase B: Vertical Micro-Migrations

Move code by functional slices (not by mass rename):

- Slice examples: actions, email, discount, quotes/invoices.
- For each slice:
  1. move small set of files/functions
  2. update imports
  3. add/adjust mirrored tests
  4. run tests
  5. commit

Exit criteria:

- Selected slice fully moved and green.

### Phase C: API Boundary Extraction

- Move endpoint handling out of monolithic controller into `api` modules.
- Keep temporary adapters for compatibility.
- Ensure service calls come from API handlers, not direct infra calls.

Exit criteria:

- Main endpoint groups mapped to dedicated API modules.

### Phase D: Cleanup and Deletions

- Remove obsolete functions/modules only when all checks pass:
  1. no references
  2. no runtime path dependency
  3. regression tests green
- Remove temporary wrappers after migration completion.

Exit criteria:

- Cleanup register emptied or explicitly accepted.

### Phase E: Closure (Finish)

- Final pass on imports and structure consistency.
- Update architecture docs and phase tracker.
- Mark Phase 4 complete.

Exit criteria:

- All DoD criteria (Section 2) satisfied.

## 4. API Reorganization Rule Set

API layer responsibilities:

- parse/validate request inputs
- call service methods
- map service result/errors to HTTP responses

API layer must avoid:

- direct persistence logic
- heavy business rules
- multi-step orchestration better suited for service layer

## 5. Endpoint Mapping Template

Use this table during migration (fill progressively):

| Endpoint               | Current Location    | Target API Module            | Target Service          | Status  |
| ---------------------- | ------------------- | ---------------------------- | ----------------------- | ------- |
| `/api/actions`         | `controller/rag.py` | `api/routes/actions.py`      | `service/action/*`      | planned |
| `/api/actions/{id}`    | `controller/rag.py` | `api/routes/actions.py`      | `service/action/*`      | planned |
| `/api/imap/*`          | `controller/rag.py` | `api/routes/email_config.py` | `service/email/*`       | planned |
| `/api/email/*`         | `controller/rag.py` | `api/routes/email.py`        | `service/email/*`       | planned |
| `/api/opportunities/*` | `controller/rag.py` | `api/routes/opportunity.py`  | `service/opportunity/*` | planned |
| `/api/quote/*`         | `controller/rag.py` | `api/routes/quote.py`        | `service/quote/*`       | planned |

## 6. Cleanup Register Template (for removals)

| Symbol/File        | Reason to Remove | Static References | Runtime Risk | Decision | Commit |
| ------------------ | ---------------- | ----------------- | ------------ | -------- | ------ |
| `example_function` | duplicate path   | none              | low          | pending  | -      |

## 7. Test Mirroring Policy

For each migrated runtime module, mirror tests by folder and behavior.

Example pattern:

- runtime: `back/src/service/email/workflow_service.py`
- tests: `back/tests/unit/service/email/test_workflow_service.py`

One test file can cover one logical function group; prefer focused tests over broad integration-style unit tests.

## 8. Working Cadence (Operational)

Each micro-step must follow:

1. code move/change
2. tests move/add/update
3. validate
4. commit

Recommended validation command set per micro-step:

- `back/venv/bin/python -m py_compile <touched_files>`
- `back/venv/bin/pytest back/tests/unit/command -q` (if command touched)
- `back/venv/bin/pytest back/tests/unit/controller -q` (if API/controller touched)
- plus domain/service/repository tests for touched slice

## 9. First Execution Batch (Suggested)

1. Finalize inventory tables (modules + endpoints).
2. Select first vertical slice: `actions`.
3. Migrate one endpoint group from controller to API route module.
4. Mirror tests and keep green.
5. Commit.

## 9.1 Execution Log (Current)

- Done: removed legacy email wrappers from `back/src/command/`:
  - `fetch_all_users_emails.py`
  - `fetch_emails.py`
  - `fetch_emails_loop.py`
- Done: removed wrapper-specific unit tests under `back/tests/unit/command/`.
- Done: updated command usage docs to `python -m src.command.email_cli ...`.
- Done: moved development server logic to `back/src/command/dev_server.py` and kept `back/dev.py` as compatibility wrapper.
- Done: moved token regeneration command to `back/src/command/regenerate_google_token.py` and kept `back/regenerate_google_token.py` as compatibility wrapper.
- Remaining: run full command regression suite in a Python environment with `pytest` available.

## 10. Back Root Cleanup (Top-level `back/` files)

Current issue:

- Too many mixed concerns live directly under `back/` (runtime code, one-off scripts, docs, tests, generated files, and local data).

Cleanup rule:

1. Keep only project-level files at `back/` root (`README`, `pyproject.toml`, `requirements.txt`, env/config roots).
2. Runtime Python code must live under `back/src/**`.
3. Operational/CLI scripts must live under `back/src/command/**` (if productized) or `back/script/**` (if internal tooling).
4. Tests must live under `back/tests/**` with mirrored structure.
5. Local runtime artifacts and credentials must remain under `back/var/**` and never be moved into source folders.
6. Generated metadata (`*.egg-info`, caches) must be ignored and excluded from architecture decisions.

### 10.1 Relocation Matrix (initial)

| Current path                            | Proposed destination                                              | Action                          | Rationale                            |
| --------------------------------------- | ----------------------------------------------------------------- | ------------------------------- | ------------------------------------ |
| `back/dev.py`                           | `back/src/command/dev_server.py`                                  | done (move + wrapper)           | productized command entrypoint       |
| `back/run_migration.py`                 | `back/src/command/run_migration.py`                               | move + wrapper                  | command should live in command layer |
| `back/regenerate_google_token.py`       | `back/src/command/regenerate_google_token.py`                     | done (move + wrapper)           | operational command                  |
| `back/extract_contact_from_file.py`     | `back/script/extract_contact_from_file.py`                        | move                            | one-off utility script               |
| `back/extract_products_from_file.py`    | `back/script/extract_products_from_file.py`                       | move                            | one-off utility script               |
| `back/test_action_cli.py`               | `back/tests/unit/command/test_action_cli.py`                      | move + rename if needed         | tests must be under tests tree       |
| `back/test_action_cli_comprehensive.py` | `back/tests/integration/command/test_action_cli_comprehensive.py` | move + classify                 | broad scenario test                  |
| `back/test_llm_model.py`                | `back/tests/integration/llm/test_llm_model.py`                    | move                            | integration-level behavior           |
| `back/test_scroll_uniqueness.py`        | `back/tests/unit/<target>/test_scroll_uniqueness.py`              | move after ownership identified | avoid tests at root                  |
| `back/TOKEN_REGENERATION.md`            | `back/README.md` section or `back/docs/token_regeneration.md`     | move/merge                      | keep operational docs grouped        |
| `back/qrant-remove.plan.md`             | `back/docs/archive/qrant-remove.plan.md`                          | archive/move                    | planning artifact, not runtime       |
| `back/rag_server.egg-info/**`           | n/a                                                               | ignore/delete local artifact    | generated packaging metadata         |
| `back/.pytest_cache/**`                 | n/a                                                               | ignore/delete local artifact    | generated test cache                 |

### 10.2 Execution Policy for Root Cleanup

For each row in the matrix:

1. Create destination module/file.
2. Add or move mirrored tests.
3. Leave temporary import/CLI wrapper in old location when needed.
4. Validate and commit.
5. Remove wrapper in a later cleanup tranche when no references remain.

---

This file is the execution contract for Phase 4: a clear start, clear end, and controlled cleanup while preserving behavior.
