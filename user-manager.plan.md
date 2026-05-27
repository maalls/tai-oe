# User Manager Plan

## Objective

Build a User Management subsection under Admin to manage application users and roles (`admin`, `user`).

`admin` can access all features.
`user` has restricted access (initially: product search + authenticated essentials only).

This plan is incremental, test-driven, and commit-oriented.

## Scope

In scope:

- Add a role model to backend profile data.
- Add admin-only APIs to list/update users and roles.
- Add frontend Admin > Users page to manage roles.
- Enforce route/API authorization by role.
- Add tests at every step (TDD-first).

Out of scope (for now):

- Fine-grained per-feature permissions matrix.
- Team/organization model.
- Audit UI beyond basic role change metadata.

## Current Baseline (observed)

- Backend has auth endpoints and profile endpoints.
- Profile table now includes `role` (`admin`|`user`) with migration `045_add_profile_role.sql` applied in local dev.
- Frontend now includes `/admin/users` route, Admin nav entry, users table, and role update actions.
- Frontend now enforces an admin UX guard on `/admin/users`.
- Backend remains the source of truth for authorization on admin APIs.

## Milestones

### Milestone 1 - Role Data Model + Read Path

Goal: Introduce role in persistence and expose it safely in user/profile payloads.

Checklist:

- [x] Add migration to extend `profile` with role (`admin` | `user`) and metadata (`updated_at` if needed).
- [x] Backfill existing users with deterministic default role.
- [x] Add DB constraint/check for valid role values.
- [x] Extend backend profile/auth DTOs to include role.
- [x] Keep compatibility for existing clients.

TDD steps:

- [x] Write failing migration/DAO tests for role read/write.
- [x] Implement migration and repository updates.
- [x] Write failing API tests for `/api/auth/user` and `/api/profile` including role.
- [x] Implement API serialization updates until tests pass.

Commit plan:

- [x] Commit 1.1: `test(role): add failing tests for role persistence and api projection`
- [x] Commit 1.2: `feat(role): add profile role column and expose role in auth/profile responses`

Acceptance criteria:

- [x] Role stored in DB and returned by user/profile APIs.
- [x] Invalid role values are rejected by DB/API.

---

### Milestone 2 - Admin Users API (Backend)

Goal: Provide admin-only endpoints to list users and update role.

Checklist:

- [x] Add `GET /api/admin/users` (id, email, full_name, role, created_at).
- [x] Add `PATCH /api/admin/users/{id}/role` with role validation.
- [x] Add authorization guard: only `admin` can call admin user endpoints.
- [x] Return explicit errors for forbidden/invalid operations.
- [x] Prevent self-demotion edge case (optional now, recommended).

TDD steps:

- [x] Write failing tests for admin guard (`403` for non-admin, `200` for admin).
- [x] Write failing tests for list endpoint shape/pagination behavior.
- [x] Write failing tests for role update validation and persistence.
- [x] Implement services/repositories/routes.

Commit plan:

- [x] Commit 2.1: `test(admin-users): add failing guard/list/update tests`
- [x] Commit 2.2: `feat(admin-users): add admin user listing and role update endpoints`

Acceptance criteria:

- [x] Non-admin users cannot access admin user APIs.
- [x] Admin can list users and change roles.
- [x] API responses are stable and validated by tests.

---

### Milestone 3 - Frontend Admin > Users UI

Goal: Add a dedicated Admin subsection for user management.

Checklist:

- [x] Add route `/admin/users`.
- [x] Add Admin navigation entry "Users".
- [x] Build users table with columns: email, full name, role, created at.
- [x] Add role update controls with optimistic UI or explicit refresh.
- [x] Handle errors/toasts/loading states.

TDD steps:

- [x] Add failing frontend unit tests for API client + state handling.
- [x] Add failing component tests for list rendering and role change flow.
- [x] Implement API client and page/component until tests pass.

Commit plan:

- [x] Commit 3.1: `test(front-admin-users): add failing ui/api tests for users management`
- [x] Commit 3.2: `feat(front-admin-users): add admin users subsection and role edit flow`

Acceptance criteria:

- [x] Admin can see/manage users in UI.
- [ ] Non-admin cannot access or use Admin Users UI.

---

### Milestone 4 - Role-Based Access Enforcement (Initial Policy)

Goal: Enforce initial role policy globally.

Initial policy:

- `admin`: full access.
- `user`: limited to product search-related features + baseline authenticated profile/session endpoints.

Checklist:

- [x] Define central permission map in backend (single source).
- [x] Add reusable role guard dependency/middleware.
- [x] Apply guard to sensitive admin/business routes.
- [x] Add frontend route guards to hide/redirect unauthorized areas.
- [x] Ensure backend is the source of truth (frontend guard is UX only).

TDD steps:

- [ ] Write failing backend authorization tests for representative routes.
- [x] Write failing frontend router guard tests for protected sections.
- [ ] Implement guards and permission map.

Commit plan:

- [ ] Commit 4.1: `test(rbac): add failing backend/frontend authorization coverage`
- [ ] Commit 4.2: `feat(rbac): enforce admin/user permissions on api and routes`

Acceptance criteria:

- [ ] `user` cannot access Admin sections/routes/APIs.
- [ ] `admin` still accesses all existing features.
- [ ] Unauthorized access returns explicit errors.

---

### Milestone 5 - Hardening, DX, and Documentation

Goal: Finalize with safety checks, observability, docs, and rollout instructions.

Checklist:

- [ ] Add edge-case tests (invalid token + role mismatch + deleted user).
- [ ] Add integration tests for end-to-end role change effect.
- [ ] Add seed/bootstrap helper to create first admin safely.
- [ ] Document role model and operational runbook.
- [ ] Add rollback strategy for migration and permission toggles.

TDD steps:

- [ ] Add failing integration/regression tests.
- [ ] Implement hardening changes until all pass.

Commit plan:

- [ ] Commit 5.1: `test(rbac-hardening): add integration and edge-case regressions`
- [ ] Commit 5.2: `docs(rbac): add user-manager runbook and bootstrap instructions`

Acceptance criteria:

- [ ] Test suite covers happy paths and common failures.
- [ ] Team can operate role model safely in dev/staging/prod.

## Cross-Cutting TDD Rules

- [ ] For each feature step: write failing test first.
- [ ] Implement smallest change to pass tests.
- [ ] Refactor only after green tests.
- [ ] Keep commits atomic and descriptive.
- [ ] Run targeted tests in each step and milestone-level smoke tests.

## Suggested Test Structure

Backend tests:

- `back/tests/unit/api/admin/users/...`
- `back/tests/unit/service/auth/...`
- `back/tests/integration/api/admin/users/...`
- `back/tests/integration/rbac/...`

Frontend tests:

- `front/tests/unit/admin/users/...`
- `front/tests/unit/router/rbac/...`
- `front/tests/integration/admin-users-flow/...`

## Progress Tracker

Use this section during implementation.

Milestone status:

- [x] M1 Role data model + read path
- [x] M2 Admin users API
- [x] M3 Frontend Admin Users UI
- [ ] M4 Role-based access enforcement
- [ ] M5 Hardening + docs

Commit tracker:

- [x] 1.1 tests
- [x] 1.2 feature
- [x] 2.1 tests
- [x] 2.2 feature
- [x] 3.1 tests
- [x] 3.2 feature
- [ ] 4.1 tests
- [ ] 4.2 feature
- [ ] 5.1 tests
- [ ] 5.2 docs

Current status notes:

- `UM-001` to `UM-009` are implemented and validated with targeted tests.
- `UM-010` is completed: reusable backend route-access dependency now centralizes token+role checks and is used by admin routes.
- `UM-011` is completed for the CSV router: RBAC backend enforcement now covers CSV endpoints via the shared route-access dependency with preserved 401/403 responses.
- `UM-012` backend source-of-truth now covers utility routes (`/api/fetch`, `/api/curl`, `/api/fs/*`, prompt reads, email fetch-loop status, and `/api/storage/*`) via the shared route-access dependency.
- `UM-012` backend source-of-truth now covers action execute/log endpoints as admin-only with 401/403 test coverage.
- `UM-012` backend source-of-truth now covers the full action router as admin-only (list/create/get/update/delete/pause/resume/execute/logs) with dedicated unit coverage.
- `UM-012` backend RBAC dependency design is now migrated to `AccessContext + RouteAccessError` with top-level FastAPI handling for 401/403 on action/admin/csv/utils routers.
- `UM-012` backend RBAC coverage now also guards opportunity stage-state updates and document status updates as admin-only, with targeted 401/403 tests.
- `UM-012` backend RBAC coverage now also guards document mutation endpoints (`storage-key`, `extract-rfp`, `update-content`, `delete`, `chat attachments`) as admin-only, with method-aware policy support for DELETE vs public GET on the same path.
- `UM-012` backend RBAC coverage now also locks the full opportunity router behind admin access, with targeted unit tests updated to supply admin auth/profile context.
- `UM-012` backend RBAC coverage now also locks the full quote router behind admin access, with targeted unit tests updated to supply admin auth/profile context.
- `UM-012` backend RBAC coverage now also keeps the `utils` router protected at the router level while removing redundant handler-level no-op access checks.
- Frontend consumers of `/api/csv/query` are aligned with RBAC by sending bearer token (Admin Database pages and Chat DB tools).
- `UM-012` is started: frontend admin route UX guard is in place for `/admin/users`.
- Remaining M4 work focuses on any missing backend route coverage outside the currently protected routers, plus the final frontend/backend polish.

## Ordered Ticket Backlog (Ready To Execute)

Estimation scale:

- `XS`: < 0.5 day
- `S`: 0.5-1 day
- `M`: 1-2 days
- `L`: 2-3 days

### Milestone 1 Tickets

1. `UM-001` Add role column to profile + constraint + backfill

- Goal: persist `admin|user` role safely in DB.
- Deliverables: migration SQL, rollback SQL, default/backfill strategy.
- TDD: failing migration/DAO test first.
- Estimate: `S`
- Depends on: none

2. `UM-002` Expose role in auth/profile payloads

- Goal: return role in `/api/auth/user` and `/api/profile`.
- Deliverables: schemas/service/router updates + API tests.
- TDD: failing endpoint contract tests first.
- Estimate: `S`
- Depends on: `UM-001`

### Milestone 2 Tickets

3. `UM-003` Create admin-only guard dependency

- Goal: reusable backend guard enforcing `admin` role.
- Deliverables: guard module, standardized forbidden response.
- TDD: failing guard unit tests first.
- Estimate: `S`
- Depends on: `UM-002`

4. `UM-004` Add `GET /api/admin/users`

- Goal: list users with `id,email,full_name,role,created_at`.
- Deliverables: route + repository query + pagination (limit/offset).
- TDD: failing list response tests first.
- Estimate: `M`
- Depends on: `UM-003`

5. `UM-005` Add `PATCH /api/admin/users/{id}/role`

- Goal: allow admin role updates with validation.
- Deliverables: payload schema, service logic, persistence update.
- TDD: failing validation and persistence tests first.
- Estimate: `M`
- Depends on: `UM-003`

6. `UM-006` Protect self-demotion and last-admin edge case

- Goal: prevent accidental lockout.
- Deliverables: guardrails in service + dedicated tests.
- TDD: failing edge-case tests first.
- Estimate: `S`
- Depends on: `UM-005`

### Milestone 3 Tickets

7. `UM-007` Add frontend API client for admin users

- Goal: typed `listUsers` and `updateUserRole` functions.
- Deliverables: API module + error normalization.
- TDD: failing API client tests first.
- Estimate: `S`
- Depends on: `UM-004`, `UM-005`

8. `UM-008` Add route `/admin/users` and nav entry

- Goal: expose Admin > Users section in UI shell.
- Deliverables: router + navigation integration + i18n labels.
- TDD: failing route/nav tests first.
- Estimate: `S`
- Depends on: `UM-007`

9. `UM-009` Build Admin Users page (table + role action)

- Goal: admin can visualize and change roles.
- Deliverables: page component, loading/error states, role change action.
- TDD: failing component behavior tests first.
- Estimate: `M`
- Depends on: `UM-008`

### Milestone 4 Tickets

10. `UM-010` Introduce backend permission map (single source)

- Goal: centralize per-role endpoint permissions.
- Deliverables: permission registry + integration in guards.
- TDD: failing permission matrix tests first.
- Estimate: `M`
- Depends on: `UM-003`

11. `UM-011` Apply backend authorization on sensitive routes

- Goal: enforce role policy beyond admin user endpoints.
- Deliverables: route guard wiring on admin/business routes.
- TDD: failing representative access tests first.
- Estimate: `L`
- Depends on: `UM-010`

12. `UM-012` Add frontend role-based route UX guard

- Goal: hide/redirect unauthorized pages for `user` role.
- Deliverables: router meta extensions + menu visibility rules.
- TDD: failing router guard tests first.
- Estimate: `M`
- Depends on: `UM-009`, `UM-011`

### Milestone 5 Tickets

13. `UM-013` Add integration regression suite for role transitions

- Goal: ensure role changes propagate immediately and safely.
- Deliverables: end-to-end backend + frontend integration checks.
- TDD: failing regression tests first.
- Estimate: `M`
- Depends on: `UM-012`

14. `UM-014` Bootstrap/runbook for first admin and recovery

- Goal: operationally safe rollout.
- Deliverables: CLI/script or SQL recipe, docs, rollback instructions.
- TDD: verify bootstrap command/script behavior.
- Estimate: `S`
- Depends on: `UM-013`

## Suggested Execution Sequence (Commit By Commit)

- [x] `UM-001` -> commit
- [x] `UM-002` -> commit
- [x] `UM-003` -> commit
- [x] `UM-004` -> commit
- [x] `UM-005` -> commit
- [x] `UM-006` -> commit
- [x] `UM-007` -> commit
- [x] `UM-008` -> commit
- [x] `UM-009` -> commit
- [ ] `UM-010` -> commit
- [ ] `UM-011` -> commit
- [ ] `UM-012` -> commit
- [ ] `UM-013` -> commit
- [ ] `UM-014` -> commit

## Effort Summary

- Backend core (`UM-001`..`UM-006`): ~5-7 dev-days
- Frontend admin UI (`UM-007`..`UM-009`): ~2-4 dev-days
- RBAC rollout (`UM-010`..`UM-012`): ~4-6 dev-days
- Hardening/docs (`UM-013`..`UM-014`): ~2-3 dev-days
- Total: ~13-20 dev-days

## Definition of Done

- [ ] Role field exists and is used consistently backend/frontend.
- [ ] Admin can manage users and roles from Admin > Users.
- [ ] User role restrictions are enforced server-side.
- [ ] Frontend reflects access limitations cleanly.
- [ ] Test coverage added for all major behavior.
- [ ] Documentation/runbook updated.
