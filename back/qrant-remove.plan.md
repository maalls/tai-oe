# Qdrant Removal Plan (Code Review + Execution)

## Objective

Remove all Qdrant-related code paths from the project, keeping only strictly necessary functionality for quote/opportunity/email/product flows.

This plan focuses on:
- removing Qdrant runtime dependencies,
- removing Qdrant API/UI surfaces,
- preventing regressions in RFQ/RFP flows,
- keeping a clean fallback for pricing/enrichment.

---

## Code Review Findings (Ordered by Severity)

## Critical findings

1. Qdrant-disable logic is currently unsafe in two enrichment loops.
- `back/src/controller/business_handler.py` and `back/src/repository/opportunity.py` both do:
  - conditional `if enable_qdrant: qdrant_handler = QdrantHandler()`
  - then unconditionally call `qdrant_handler.scroll_points(...)` in a loop.
- If `ENABLE_QDRANT=false`, `qdrant_handler` is undefined and the code falls into exception handling.
- This masks behavior and can still produce noisy error paths.

2. Request error handling can cascade after socket disconnect.
- `back/src/controller/rag.py` `json()` calls `_send_error()` on write failures.
- `_send_error()` writes to the same possibly broken stream.
- This creates `BrokenPipeError` cascades and duplicate traces.
- Not Qdrant-specific, but heavily surfaced during Qdrant failures.

## High findings

3. Qdrant route surface is still publicly wired.
- `GET /api/qdrant` and `GET /api/embeddings` still route through `handlers` in `back/src/controller/rag.py`.
- These should be removed entirely (not just guarded by a flag) if Qdrant is removed.

4. Backend domain logic still couples quote generation to Qdrant enrichment.
- RFQ/RFP extraction enriches product prices via Qdrant in:
  - `back/src/controller/business_handler.py`
  - `back/src/repository/opportunity.py`
- This must be replaced by a deterministic non-vector fallback (DB lookup / no-price mode).

5. Product write path is Qdrant-coupled.
- `back/src/controller/product/product.py` performs `upsert_in_qdrant()` after DB upsert.
- Removing Qdrant requires removing this side effect and related model imports.

## Medium findings

6. Multiple Qdrant implementation files remain active and/or importable.
- `back/src/controller/qdrant_handler.py`
- `back/src/controller/qdrant_handlers.py`
- `back/src/controller/qdrant_query_ops.py`
- `back/src/controller/qdrant_filter.py`
- `back/src/qdrant_client_wrapper.py`
- `back/src/command/qdrant_cli.py`
- `back/src/csv_to_qdrant.py`

7. Frontend still contains Qdrant UI and tool integrations.
- Admin pages, tool executor hooks, chat vector search helpers, and routes reference `/api/qdrant`.
- These must be removed to avoid dead UI paths and runtime errors.

8. Qdrant docs/tests/config remain and will become stale/noise after removal.
- Docs: `back/docs/QDRANT_*.md`
- Tests/scripts: `back/test_qdrant_refciales.py`, `back/src/controller/tests/test_qdrant_handler.py`
- Config/deps: `QDRANT_*` env/config entries and `qdrant-client` dependency.

---

## Removal Scope (Strict Necessary)

## Remove from backend runtime

- API endpoints:
  - remove `/api/qdrant`
  - remove `/api/embeddings` only if it is not needed by non-Qdrant features
- Orchestrator wiring:
  - remove `QdrantHandler`/`QdrantHandlers` imports and fields from `RequestHandlers`
- Domain coupling:
  - remove Qdrant enrichment branches from RFQ/RFP flows
  - remove Qdrant upsert from product controller

## Remove implementation files

- delete all backend Qdrant implementation and CLI/export helpers listed above.

## Remove from frontend

- remove Qdrant admin pages and routes:
  - `front/src/components/admin/components/qdrant/*`
  - `front/src/components/qdrant/*`
  - `front/src/router/index.ts` qdrant routes
  - nav entries in admin header
- remove chat/tool integrations that call `/api/qdrant`:
  - `front/src/components/chat/toolExecutor.ts`
  - `front/src/components/chat/vectorSearch.ts`
  - `front/src/qdrant-chat-integration.ts`
  - `front/src/utils/qdrantSearch.ts`
- remove i18n keys for qdrant pages/tools if unused

## Remove config/dependencies/docs/tests

- `back/requirements.txt`: remove `qdrant-client`
- `back/pyproject.toml`: remove `qdrant-client` dependency
- `back/.env` and `back/config.yml`: remove `QDRANT_*` and `qdrant` block
- delete Qdrant-only docs and tests/scripts

---

## Required Replacement Behavior (Post-Removal)

For RFQ/RFP quote generation and opportunity enrichment:

1. Keep extraction flow operational without vector search.
2. Replace Qdrant price lookup with one of:
- DB-only exact/ILIKE lookup by `sku` + optional brand,
- no enrichment mode (leave `price=None`) with explicit metadata `price_found=false`.
3. Ensure returned payload shape remains backward compatible where possible.

Recommendation:
- Prefer DB lookup fallback first, then no-price fallback.

---

## Execution Plan

## Phase 1: Safe decoupling (no deletes yet)

1. Remove Qdrant calls from RFQ/RFP paths and product upsert side effects.
2. Remove `/api/qdrant` and `/api/embeddings` route wiring from `rag.py` and `handlers.py`.
3. Ensure endpoint responses are still valid for existing frontend screens not related to qdrant.

Exit criteria:
- RFQ import works with no Qdrant log lines.
- No `/api/qdrant` route in backend.

## Phase 2: Delete Qdrant modules and imports

1. Delete backend Qdrant modules and scripts.
2. Remove stale imports across backend.
3. Remove Qdrant env/config/dependency entries.

Exit criteria:
- Project imports cleanly with no `qdrant` references in backend runtime modules.

## Phase 3: Frontend cleanup

1. Remove Qdrant pages/routes/nav entries.
2. Remove chat qdrant tool hooks and utility modules.
3. Rebuild frontend and validate no dead links/routes.

Exit criteria:
- No `qdrant` pages in UI.
- No network calls to `/api/qdrant`.

## Phase 4: Test and verification

1. Update/delete Qdrant tests.
2. Add/adjust regression tests for:
- RFQ/RFP generation without vector enrichment,
- opportunity search/create flows,
- product creation flow without Qdrant side effects.
3. Run backend and frontend test suites + smoke tests.

Exit criteria:
- Green tests, clean logs, no Qdrant dependency at runtime.

---

## Validation Checklist

- `grep -R "qdrant" back/src` returns zero runtime references (excluding optional archived docs if intentionally kept).
- `grep -R "qdrant" front/src` returns zero active feature references.
- RFQ import endpoint succeeds without Qdrant logs/errors.
- No `qdrant-client` in dependency manifests.
- Frontend build passes and app routes load without missing-component errors.

---

## Risks and Mitigations

- Risk: quote totals degrade if pricing enrichment disappears.
  - Mitigation: implement DB fallback pricing before deleting Qdrant code.

- Risk: frontend chat/admin features break due to removed tools/routes.
  - Mitigation: remove navigation entries and tool registration in same change set.

- Risk: hidden imports remain in scripts/tests causing CI failures.
  - Mitigation: run repository-wide `qdrant` search and clean all references in one pass.

---

## Suggested PR Breakdown

1. PR1: Decouple RFQ/RFP/product runtime logic from Qdrant.
2. PR2: Remove backend Qdrant routes/modules/dependencies/config.
3. PR3: Remove frontend Qdrant UI/tools/routes and rebuild.
4. PR4: Test/doc cleanup and final verification.
