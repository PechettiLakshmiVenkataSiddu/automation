# Phase 2 — System Architecture

This package defines the target architecture for Aether. It proceeds directly from the approved Phase 0 product foundation at the request of the product owner. Phase 1 (Software Requirements Specification) remains deferred; this architecture uses the Phase 0 requirements as its current source of truth and must be reconciled with the SRS when Phase 1 is completed.

## Deliverables

- [System context](system-context.md)
- [Container architecture](container-architecture.md)
- [Component architecture](component-architecture.md)
- [Data flows](data-flows.md)
- [Security architecture](security-architecture.md)
- [Operational architecture](operational-architecture.md)

## Architecture invariants

1. PostgreSQL is the authoritative store for business and security state.
2. Every request and asynchronous job carries an authenticated workspace context.
3. No external side effect may bypass policy evaluation, approval requirements, audit recording, or idempotency handling.
4. AI providers, connectors, and executors are adapters behind domain-defined contracts.
5. Browser, desktop, and arbitrary-code execution never runs in the API process.
6. Sensitive data is minimized, encrypted, redacted from logs, and retained only under an explicit policy.
