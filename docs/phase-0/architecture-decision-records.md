# Architecture Decision Records

## ADR-001 — Modular monolith first

**Status:** Accepted

**Context:** The platform has many domains but early delivery requires transactional consistency, rapid iteration, and low operational overhead.

**Decision:** Build the backend as a modular FastAPI monolith with strict domain boundaries, explicit module APIs, and asynchronous worker processes. Extract services only when measured scaling, ownership, or isolation needs justify it.

**Consequences:** Development and local operations remain simpler. Modules must not use direct cross-domain persistence access, preventing a later service split from becoming prohibitively expensive.

**Reconsider when:** Independent domain deployment, data residency, or workload scale cannot be satisfied by the modular monolith.

## ADR-002 — PostgreSQL is the system of record

**Status:** Accepted

**Context:** Identity, workflow state, approvals, billing-related usage, and audit metadata need transactional integrity.

**Decision:** Store authoritative relational state in PostgreSQL, accessed through SQLAlchemy and migrated through Alembic. Use Redis only for ephemeral coordination and ChromaDB only for vector retrieval indexes.

**Consequences:** Every non-relational store has a rebuild or reconciliation path from PostgreSQL and managed object storage.

**Reconsider when:** Verified throughput or data-model constraints require a specialized authoritative store.

## ADR-003 — Queue-backed execution

**Status:** Accepted

**Context:** Workflows and tool calls may outlive HTTP requests and require retries and isolation.

**Decision:** Dispatch durable work through Celery with Redis as the initial broker/result transport; persist the authoritative run state in PostgreSQL. APScheduler is limited to scheduling and enqueuing jobs, not executing business work inline.

**Consequences:** Workers scale independently and executions survive API restarts. Queue health becomes a production dependency.

**Reconsider when:** Execution volume, scheduling semantics, or workflow durability require a different orchestration engine.

## ADR-004 — Policy and approval before tool execution

**Status:** Accepted

**Context:** AI-generated plans can cause external effects and require dependable human control.

**Decision:** Every tool invocation is evaluated against role, connector scope, risk class, workspace policy, and runtime context. Actions that match an approval policy enter a durable pending-approval state and cannot execute until approved.

**Consequences:** Tool adapters require declarative risk metadata and idempotency support. Some flows need asynchronous interaction design.

**Reconsider when:** Regulatory or customer policy requirements demand an external policy engine.

## ADR-005 — Provider abstraction with explicit data boundaries

**Status:** Accepted

**Context:** Users may choose OpenAI, Anthropic, Gemini, or local Ollama models with different capabilities and retention conditions.

**Decision:** Define a provider-neutral model gateway that normalizes requests, streaming, usage, tool calls, errors, and capability declarations while retaining provider-specific configuration outside domain logic.

**Consequences:** Providers are replaceable and model routing is centrally auditable. Lowest-common-denominator abstractions are avoided through named capabilities.

**Reconsider when:** A provider's differentiated feature becomes an essential domain primitive.

## ADR-006 — Browser and desktop automation are isolated executors

**Status:** Accepted

**Context:** Browser and desktop control introduce elevated data and operational risk.

**Decision:** Run these capabilities in isolated, short-lived execution environments with scoped credentials, network restrictions, artifact capture, and explicit approval for sensitive interactions. The control plane never executes arbitrary desktop or browser work in the API process.

**Consequences:** Deployment is more complex but blast radius and evidence quality improve.

**Reconsider when:** A hardened managed execution platform replaces custom sandboxing.
