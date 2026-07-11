# Phase 3 — Repository Structure

## Purpose

This phase establishes the monorepo boundaries and contributor contracts required to implement the architecture safely. It does not introduce product features, database schema, authentication, or deployable services; those begin in their designated phases.

## Top-level layout

```text
automation/
├── apps/
│   ├── api/                 FastAPI control plane
│   ├── web/                 Next.js web application
│   ├── worker/              Celery worker entrypoints and workload configuration
│   └── scheduler/           APScheduler entrypoint and leader coordination
├── packages/
│   ├── contracts/           Versioned TypeScript API and event contracts
│   ├── ui/                  Shared accessible design-system components
│   └── config/              Shared frontend/tooling configuration
├── services/
│   └── executor/            Isolated browser, desktop, and constrained-code executor
├── backend/
│   ├── src/aether/          Python domain, application, infrastructure, and interfaces
│   └── tests/               Backend test suites by test type
├── infra/
│   ├── docker/              Local/container image definitions
│   ├── nginx/               Edge proxy configuration
│   ├── compose/             Docker Compose environments
│   └── monitoring/          Metrics, dashboards, alerts, and tracing configuration
├── docs/                    Phase documents and enduring architecture records
├── scripts/                 Repeatable developer and CI utility scripts
└── .github/workflows/       CI/CD workflows
```

## Backend module layout

```text
backend/src/aether/
├── domain/                  Entities, value objects, domain events, policies
├── application/             Use cases, commands, queries, ports, DTOs
├── infrastructure/          SQLAlchemy, queues, providers, connectors, storage
├── interfaces/              FastAPI routes, dependencies, request/response schemas
├── bootstrap/               Composition root, configuration, lifecycle
└── shared/                  Cross-cutting safe primitives: IDs, errors, observability
```

Domain modules such as identity, conversations, knowledge, automation, integrations, governance, and notifications are represented consistently inside the appropriate layer. Cross-module persistence writes are prohibited; cross-module coordination uses application ports and domain events.

## Dependency rules

1. `domain` imports neither frameworks nor database/provider SDKs.
2. `application` depends on domain abstractions and ports, never concrete infrastructure.
3. `infrastructure` implements application ports and may depend on external libraries.
4. `interfaces` translates transport concerns to application commands/queries.
5. Applications may consume shared packages; shared packages may not import applications.
6. The executor communicates through versioned contracts and does not share the control-plane database.

## Validation policy

| Area          | Required validation                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------- |
| TypeScript    | Formatting, ESLint, TypeScript strict type-check, unit tests.                                     |
| Python        | Ruff formatting/linting, mypy strict type-check, pytest.                                          |
| API contracts | Contract validation and backward-compatibility checks before public changes.                      |
| Security      | Dependency review, secret scanning, static analysis, and authorization-focused tests as relevant. |
| Database      | Alembic migration validation and integration tests once the data layer is introduced.             |

## Phase exit criteria

1. The directory boundaries and dependency rules are documented and reflected in version-controlled configuration.
2. JavaScript/TypeScript workspace management and Python package metadata are reproducible.
3. Formatting, linting, and type-check commands have a stable root-level interface.
4. No product, database, or authentication feature has been fabricated ahead of its phase.
