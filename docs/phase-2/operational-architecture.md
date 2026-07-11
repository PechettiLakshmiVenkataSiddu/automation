# Operational Architecture

## Reliability model

- APIs are stateless and may be restarted or scaled without losing accepted work.
- A command is durable only after its transaction, run/intent record, and outbox entry commit together.
- Workers claim work with leases, persist state after each meaningful transition, and use retry policies that distinguish transient from permanent failures.
- Connector and provider calls have bounded timeouts, circuit breakers, rate limits, and classified errors.
- Irreconcilable jobs enter a dead-letter workflow with an operator-visible incident record; they are never silently discarded.

## Observability

| Signal          | Required fields / use                                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Structured logs | Timestamp, severity, service, environment, correlation ID, workspace pseudonym, actor pseudonym, event, duration, outcome.            |
| Metrics         | Request rate/latency/errors, queue depth/age, job completion/retries, provider usage/latency/errors, approval aging, executor health. |
| Traces          | Request-to-worker-to-connector path with redacted attributes and propagation across asynchronous boundaries.                          |
| Audit events    | Immutable record of security and external-effect events; separate from diagnostic logs.                                               |
| Health checks   | Liveness, readiness, dependency reachability, queue readiness, migration version, and executor capacity.                              |

## Backup and recovery

PostgreSQL receives point-in-time recovery backups and regular restore verification. Object storage versioning and lifecycle rules protect files and artifacts. Redis and ChromaDB are reconstructible from authoritative records, source files, and documented ingestion/rebuild processes. Recovery objectives and provider-specific implementation targets are finalized in Phase 24 before production deployment.

## Deployment environments

| Environment | Purpose                                                         | Data policy                                                                |
| ----------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Local       | Developer iteration and automated tests.                        | Synthetic data and local secrets only.                                     |
| CI          | Reproducible build, test, security scans, and migration checks. | Ephemeral synthetic data only.                                             |
| Staging     | Integration, performance, security, and release validation.     | Sanitized or synthetic data; isolated credentials.                         |
| Production  | Customer workloads.                                             | Managed secrets, encrypted data, backups, monitoring, and access controls. |

## Change management

Database migrations are forward-compatible, reviewed, tested against production-like data volume, and paired with rollback/roll-forward instructions. API changes use explicit compatibility policies. Infrastructure and dependency changes pass automated checks and protected review. Emergency changes are audited and receive retrospective review.
