migrate the backend (folder back) to use FastAPI

strategy
the goal is to replace the current custom http server transport with FastAPI while keeping the existing business logic, handlers, repositories, and services as much as possible.

principles

- reuse the current domain and application code instead of duplicating it in a parallel api stack.
- introduce fastapi as the new entrypoint and move routes gradually.
- keep compatibility with the existing frontend api contract until each endpoint is explicitly migrated.
- add pydantic request and response models early so the contract becomes explicit.
- use tests to lock the current behavior before replacing each route group.

pydantic strategy

- use pydantic v2 for all http input and output schemas.
- keep pydantic models at the api boundary only; do not move business rules into schemas.
- create one schema module per domain or route group instead of one giant shared dto module.
- prefer small request models and explicit response models over untyped dict payloads.
- use `ConfigDict(from_attributes=True)` when serializing domain objects into responses.
- keep domain entities, repositories, and services independent from pydantic unless a boundary conversion is needed.

first schemas to create

- auth: login, signup, logout, oauth callback, current user.
- email: gmail authorize, callback, list messages, classify, send email, attachments, delete, resync.
- quote: submit quote, list quotes, download quote file, generate pdf.
- utility endpoints: fetch, curl, fs create/read, prompt, storage metadata and download helpers.

schema conventions

- name request models after the action, such as `LoginRequest`, `SendEmailRequest`, `QuoteSubmitRequest`.
- name response models after the returned resource or action result, such as `UserResponse`, `EmailMessageResponse`, `QuoteResponse`.
- use `str | None`, `list[str]`, and typed nested models instead of raw dictionaries where the payload shape is known.
- keep compatibility fields in the response if the frontend still depends on the existing shape.

recommended structure

- create a FastAPI app entrypoint for the backend server.
- keep legacy transport and new transport in separate folders so ownership is explicit.
- keep shared dependencies, auth helpers, and service factories in reusable modules.
- keep the existing domain handlers and services as the source of truth for business rules.

folder strategy (legacy vs new)

- keep legacy http.server transport in `src/api/**` as read-only except for critical fixes.
- put new FastAPI transport in `src/api_fastapi/**`.
- keep shared business code outside transport folders (`src/service/**`, `src/repository/**`, `src/domain/**`).
- for each migrated route group, add the new router under `src/api_fastapi/<domain>/router.py` and schemas under `src/api_fastapi/<domain>/schemas.py`.
- avoid copying handler logic from `src/api/**`; call shared services or handlers through adapters when needed.

route migration tracking

- maintain a route migration matrix in this file with columns: route, legacy owner, fastapi owner, status, parity tests.
- allowed status values: `legacy`, `dual`, `fastapi`, `retired`.
- only mark `fastapi` when tests pass and frontend calls are confirmed against new endpoint behavior.

progress snapshot

- tracked route groups: `13`
- fully migrated to FastAPI: `13/13` (`100%`)
- still in dual mode: `0/13`
- still legacy only: `0/13`
- progress bar: `[#############] 13/13`
- cleanup pass (`2026-05-18`): removed redundant POST legacy dispatch branches (opportunity/document/quote duplicates) and removed orphan DDD helper methods from `src/api/router.py`; dispatcher + fastapi/rag regression tests green.

priority tracker

| area               | state                          | note                                                                                      |
| ------------------ | ------------------------------ | ----------------------------------------------------------------------------------------- |
| auth               | done for current backend scope | auth and oauth endpoints served by FastAPI; legacy auth routing removed                   |
| settings + utility | mostly done                    | imap, fetch-loop, storage metadata/download, csv upload, fetch/curl/fs/prompt migrated    |
| email              | mostly done                    | Gmail and IMAP are on FastAPI; attachment/classify/resync flows still legacy              |
| quote              | done for current backend scope | submit, send, list, update, pdf, download migrated                                        |
| client/opportunity | mostly done                    | DDD opportunity and RFP get/submit migrated; some broader opportunity routes still legacy |
| vendor             | in progress                    | DDD vendor get migrated; broader vendor/client data access still to review                |
| storage upload     | done for current backend scope | csv source upload migrated to FastAPI                                                     |

current route matrix

| route group                                                                                          | legacy owner                                   | fastapi owner                   | status    | parity tests                                                                                                    |
| ---------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------- |
| `/api/auth/*`                                                                                        | retired from legacy dispatcher                 | `src/api_fastapi/auth/*`        | `fastapi` | `tests/unit/api_fastapi/auth/router/*`, `tests/integration/api/fastapi/test_app.py`                             |
| `/api/gmail/*`                                                                                       | retired from legacy dispatcher                 | `src/api_fastapi/email/*`       | `fastapi` | `tests/unit/api_fastapi/email/router/test_gmail_routes.py`, `tests/integration/api/fastapi/test_app.py`         |
| `/api/imap/*` (settings)                                                                             | retired from legacy dispatcher                 | `src/api_fastapi/email/*`       | `fastapi` | `tests/unit/api_fastapi/email/router/test_gmail_routes.py`                                                      |
| `/api/email-fetch-loop/status`                                                                       | retired from legacy dispatcher                 | `src/api_fastapi/utils/*`       | `fastapi` | `tests/unit/api_fastapi/utils/router/test_utils_routes.py`                                                      |
| `storage upload flow` (`/api/csv/source` POST)                                                       | retired from legacy CSV POST route             | `src/api_fastapi/csv/*`         | `fastapi` | `tests/unit/api_fastapi/csv/router/test_csv_routes.py`, `tests/integration/api/file/test_upload_integration.py` |
| `storage metadata/download` (`/api/storage/*` GET/HEAD)                                              | retired from legacy dispatcher                 | `src/api_fastapi/utils/*`       | `fastapi` | `tests/unit/api_fastapi/utils/router/test_utils_routes.py`                                                      |
| `quote submit/send/list` (`/api/quote`, `/api/quote/send`, `/api/quotes/list`)                       | retired from legacy dispatcher                 | `src/api_fastapi/quote/*`       | `fastapi` | `tests/unit/api_fastapi/quote/router/test_quote_routes.py`                                                      |
| `quote doc update/pdf/download` (`/api/quote/{id}`, `/api/quote/{id}/pdf`, `/api/quotes/download/*`) | retired from legacy dispatcher                 | `src/api_fastapi/quote/*`       | `fastapi` | `tests/unit/api_fastapi/quote/router/test_quote_routes.py`                                                      |
| `vendor ddd get` (`/api/ddd/vendor`)                                                                 | retired from legacy DDD route map              | `src/api_fastapi/vendor/*`      | `fastapi` | `tests/unit/api_fastapi/vendor/router/test_vendor_routes.py`                                                    |
| `opportunity ddd get/advance` (`/api/ddd/opportunity`, `/api/ddd/opportunity/advance`)               | retired from legacy DDD route maps             | `src/api_fastapi/opportunity/*` | `fastapi` | `tests/unit/api_fastapi/opportunity/router/test_opportunity_routes.py`                                          |
| `rfp ddd get/submit` (`/api/ddd/rfp`, `/api/ddd/rfp/submit`)                                         | retired from legacy DDD route maps             | `src/api_fastapi/rfp/*`         | `fastapi` | `tests/unit/api_fastapi/rfp/router/test_rfp_routes.py`                                                          |
| rag upload processing flow (`/api/rfp` upload, `/api/rfq/generate`)                                  | retired from legacy RFQ POST dispatcher        | `src/api_fastapi/rfq/*`         | `fastapi` | `tests/unit/api_fastapi/rfq/router/test_rfq_routes.py`, `tests/integration/api/rag/test_rag.py`                 |
| utility endpoints (`/api/fetch`, `/api/curl`, `/api/fs/*`, `/api/prompt`)                            | `fetch/curl/fs retired from legacy dispatcher` | `src/api_fastapi/utils/*`       | `fastapi` | `tests/unit/api_fastapi/utils/router/test_utils_routes.py`                                                      |

migration order
prioritize endpoints based on what the frontend actually needs, starting with the most visible and central flows.

priority order:

- login and auth
- settings and environment-dependent endpoints
- email section
- quote section and subsection
- client section and subsection
- vendor section and subsection
- storage, prompt, fetch, curl, and other utility endpoints used by the app

migration approach

1. inventory the frontend api calls and map them to current backend routes.
2. define pydantic schemas for the first route group.
3. create fastapi routers for one small slice at a time.
4. route each endpoint to the existing handler or service layer.
5. keep the old server working until the migrated endpoints are stable.
6. remove the old transport only after the fastapi app covers the required contract.

note on direct supabase calls

- direct Supabase calls from the frontend will be reviewed and reduced last, after the backend FastAPI migration and legacy transport cleanup are complete.
- until then, do not expand direct Supabase usage for new business workflows; prefer FastAPI for new backend-facing behavior.
- once the backend refactor is finished, run a dedicated pass to classify remaining direct Supabase calls into `keep-direct`, `migrate-soon`, and `migrate-now`.

cleanup protocol

1. when a route group reaches `fastapi`, freeze legacy files for that group.
2. run parity tests for legacy vs fastapi responses on critical scenarios.
3. switch dispatcher/entrypoint mapping to fastapi only for that group.
4. remove dead legacy handlers/routes for the migrated group in a dedicated cleanup commit.
5. run full unit and integration test suites.
6. repeat by route group until no active route remains in legacy transport.

testing strategy

- add contract-style tests for each migrated endpoint.
- keep the current unit tests for business logic.
- add integration tests for auth, email, quote, and storage flows before deleting the old server.
- prefer tests that mirror the real route structure so the migration stays easy to navigate.

risks to watch

- do not split logic across a new fastapi layer and the old server layer.
- do not migrate only the visible pages and forget utility endpoints used by the frontend runtime.
- do not accept broad breaking changes unless the frontend has a planned update at the same time.

definition of done

- the backend starts with fastapi instead of the custom http.server entrypoint.
- the important frontend flows work against the new api.
- the old server path is removed or kept only as a temporary compatibility layer.
- the most important routes have automated tests covering the new contract.
