# Functional, Non-functional, and Acceptance Requirements

## Functional requirements

| ID    | Requirement                                                                                                                                                                     |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-01 | The system shall authenticate users through Google OAuth and GitHub OAuth, issue short-lived access tokens and rotating refresh tokens, and support sign-out from all sessions. |
| FR-02 | The system shall enforce organization and workspace isolation plus role-based authorization for every API and background task.                                                  |
| FR-03 | The system shall provide model-routed AI chat with persisted conversations, streaming responses, tool-call visibility, and configurable provider credentials.                   |
| FR-04 | The system shall manage user-uploaded files, knowledge collections, ingestion status, retrieval citations, and deletion.                                                        |
| FR-05 | The system shall allow users to create, version, validate, schedule, activate, pause, and clone workflows.                                                                      |
| FR-06 | The system shall execute workflows asynchronously with durable state, retry policy, idempotency keys, cancellation, and run logs.                                               |
| FR-07 | The system shall provide connectors for approved external services and store their credentials encrypted with narrowly scoped authorization.                                    |
| FR-08 | The system shall gate sensitive tool actions through policy evaluation and human approval when required.                                                                        |
| FR-09 | The system shall record security-relevant and externally consequential events in an append-only audit trail.                                                                    |
| FR-10 | The system shall expose notifications, activity history, API key lifecycle management, admin functions, and usage analytics according to role.                                  |

## Non-functional requirements

| Category        | Requirement                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------- |
| Security        | Follow OWASP ASVS-aligned controls; encrypt secrets at rest; use TLS in transit; never log credentials or raw tokens. |
| Availability    | Target 99.9% monthly availability for control-plane APIs, excluding announced maintenance.                            |
| Performance     | API reads at p95 under 400 ms excluding provider calls; workflow dispatch at p95 under 2 seconds.                     |
| Scalability     | Horizontally scale API and worker processes; jobs must not depend on in-memory process state.                         |
| Reliability     | Use transactional persistence, idempotency, exponential backoff, dead-letter handling, and resumable execution state. |
| Privacy         | Support data export, erasure, retention policy, consent withdrawal, and per-tenant data boundaries.                   |
| Observability   | Emit structured logs, metrics, traces, health checks, and correlation IDs across API, worker, and integration calls.  |
| Accessibility   | Meet WCAG 2.2 AA for the user-facing web application.                                                                 |
| Maintainability | Enforce typed interfaces, automated tests, linting, migration discipline, and documented public contracts.            |

## Phase-level acceptance criteria

Phase 0 is accepted when the following decisions are unambiguous and approved:

1. The target users, primary jobs, and the initial product boundary are documented.
2. Functional and quality requirements establish measurable behavior for later specifications.
3. Material architectural choices include context, decision, consequences, and reconsideration triggers.
4. Major security, reliability, vendor, and compliance risks have owners and mitigations.
5. The milestone sequence identifies dependencies and completion gates before implementation begins.

## Product acceptance criteria for the initial release

1. A user can authenticate, create a workspace, and use only data authorized for that workspace.
2. A user can complete a workflow whose external effect is visible in the run history and audit trail.
3. A policy-required action cannot execute without valid approval, and rejected approvals prevent execution.
4. Revoking an integration prevents new uses of its credential and records the revocation.
5. An administrator can identify the actor, policy decision, request correlation ID, and outcome for a sensitive action.
6. A user can export and delete their personal data through product controls, subject to required retention policies.
