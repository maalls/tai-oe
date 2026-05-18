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
- organize api code by domain modules and routers, not by a second duplicate "fastapi" copy of every layer.
- keep shared dependencies, auth helpers, and service factories in reusable modules.
- keep the existing domain handlers and services as the source of truth for business rules.

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
