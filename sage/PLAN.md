# Sage Integration Technical Plan

Behavior and execution style are defined in [.github/instructions/sage.instructions.md](.github/instructions/sage.instructions.md).
This file focuses only on the technical roadmap and checkpoints.

## Final Goal

From the Ai Oe server:

1. Query Sage data (starting with clients).
2. Post Sage data (starting with quotes).
3. Run with reliable logs, error handling, retries, and safe configuration.

## Phase 0 - Environment Baseline

### 0.1 Verify .NET tooling

Actions:

1. ~~Run `dotnet --info`.~~
2. ~~Run `dotnet --list-sdks`.~~
3. ~~Confirm work happens under `sage/`.~~

Checkpoint:

1. SDK available and commands succeed.

### 0.2 Confirm project location and naming

Actions:

1. ~~Confirm target project name: `AiOe.SageService`.~~
2. ~~Confirm target path under `sage/`.~~
3. ~~Move solution file to `sage/rag.sln` and fix project relative path.~~

Checkpoint:

1. Naming/location frozen before scaffolding.

## Phase 1 - First Runnable Service

### 1.1 Scaffold worker project

Actions:

1. ~~Run `dotnet new worker -n AiOe.SageService`.~~

Checkpoint:

1. Project exists with `Program.cs`, `Worker.cs`, and `appsettings.json`.

### 1.2 Run template unchanged

Actions:

1. ~~`cd AiOe.SageService`~~
2. ~~`dotnet run`~~

Checkpoint:

1. Service starts and logs normally.

### 1.3 Read default startup flow

Actions:

1. Review `Program.cs`.
2. Review `Worker.cs`.
3. Review `appsettings.json`.

Checkpoint:

1. Clear understanding of host startup, worker loop, and config loading.

## Phase 2 - Minimal Structure (No Real Sage Calls Yet)

### 2.1 Add folders for clean organization

Actions:

1. Create `Contracts/`.
2. Create `Clients/`.
3. Create `UseCases/`.
4. Create `Infrastructure/`.
5. Create `Models/`.

Checkpoint:

1. App still runs unchanged.

### 2.2 Define first Sage client contract

Actions:

1. Add `Contracts/ISageClient.cs`.
2. Include one read method signature only.

Checkpoint:

1. Project builds without implementing network code.

### 2.3 Add fake Sage client

Actions:

1. Add `Clients/FakeSageClient.cs`.
2. Return hardcoded sample client response.

Checkpoint:

1. Worker can call fake client and log returned data.

## Phase 3 - First Real Read Operation (Clients)

### 3.1 Freeze Sage API facts

Actions:

1. Document base URL.
2. Document auth method.
3. Document client lookup endpoint.
4. Document required headers.
5. Document sample request/response.

Checkpoint:

1. A short verified API reference exists under `sage/`.

### 3.2 Add Sage configuration keys

Actions:

1. Add `Sage:BaseUrl`.
2. Add `Sage:AuthType`.
3. Add `Sage:ApiKey` (or token placeholders).
4. Add `Sage:TimeoutSeconds`.

Checkpoint:

1. Config values can be read from app configuration.

### 3.3 Register typed HttpClient

Actions:

1. Register Sage client with DI and HttpClient.

Checkpoint:

1. Project builds and resolves Sage client from DI.

### 3.4 Implement `GetClientByCode`

Actions:

1. Implement one real HTTP read method only.
2. Add request/response/error logs.

Checkpoint:

1. Manual test retrieves a real Sage client or returns a clear error.

### 3.5 Add timeout and minimal retry

Actions:

1. Enforce request timeout.
2. Add small retry policy for transient failures.

Checkpoint:

1. Transient network errors retry; terminal failures are explicit.

## Phase 4 - Expose to Ai Oe Server

### 4.1 Add first read endpoint

Actions:

1. Expose `GET /sage/clients/{code}`.
2. Wire endpoint to Sage client use case.

Checkpoint:

1. Ai Oe can query one client through the service.

### 4.2 Add quote endpoint as safe stub

Actions:

1. Expose `POST /sage/quotes`.
2. Validate payload.
3. Return mock success (no Sage write yet).

Checkpoint:

1. End-to-end request path exists without side effects.

## Phase 5 - Real Quote Posting

### 5.1 Define mapping from Ai Oe quote to Sage payload

Actions:

1. Add mapping model(s).
2. Validate required fields and formats.

Checkpoint:

1. Mapping is explicit and testable.

### 5.2 Implement real `PostQuoteAsync`

Actions:

1. Implement Sage write call.
2. Log correlation id and Sage response metadata.

Checkpoint:

1. One quote posts successfully in target environment.

### 5.3 Add idempotency guard

Actions:

1. Add idempotency/correlation strategy.

Checkpoint:

1. Repeated submit does not create duplicate quotes.

## Phase 6 - Reliability and Operations

### 6.1 Standardize error model

Actions:

1. Define service error envelope.
2. Map Sage errors to predictable response format.

Checkpoint:

1. Errors are consistent and actionable.

### 6.2 Add health endpoints

Actions:

1. Add liveness endpoint.
2. Add readiness endpoint (includes Sage dependency check policy).

Checkpoint:

1. Service can be monitored and orchestrated safely.

### 6.3 Add tests

Actions:

1. Unit tests for mapping and validation.
2. Integration tests for Sage client wrapper.

Checkpoint:

1. Core read/write paths have automated coverage.

## Phase 7 - Security and Deployment

### 7.1 Secure configuration

Actions:

1. Move secrets to env/secret store.
2. Ensure no secrets in source control.

Checkpoint:

1. Security baseline passes review.

### 7.2 Local/dev runbook

Actions:

1. Add startup commands.
2. Add required env variables list.
3. Add troubleshooting notes.

Checkpoint:

1. Another developer can run the service quickly.

### 7.3 Release checklist

Actions:

1. Define pre-release checks.
2. Define rollback strategy.

Checkpoint:

1. First deployment can be executed safely.

## Done Criteria

The initiative is complete when:

1. Ai Oe can fetch a client through Sage service.
2. Ai Oe can post a quote through Sage service.
3. Logs include correlation ids and clear failure reasons.
4. Config is externalized and secure.
5. Minimal tests pass in CI/local.
