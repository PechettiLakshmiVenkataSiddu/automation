# Risk Analysis

Risk scale: likelihood and impact are Low, Medium, or High. Owners are accountable for mitigation design during the indicated phase.

| ID   | Risk                                                             | Likelihood | Impact | Mitigation                                                                                                                            | Owner              | Phase     |
| ---- | ---------------------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------- |
| R-01 | Prompt injection causes unsafe tool actions or data disclosure.  | High       | High   | Treat external content as untrusted; isolate tool permissions; policy-check every action; require confirmation for sensitive effects. | Security           | 9, 11, 16 |
| R-02 | OAuth tokens or API secrets are exposed.                         | Medium     | High   | Envelope encryption, secret redaction, least-privilege scopes, rotation, vault-backed production keys, and security tests.            | Security           | 5, 6      |
| R-03 | Tenant data crosses workspace boundaries.                        | Medium     | High   | Tenant context on every request/job, authorization tests, database constraints, query review, and audit alerts.                       | Backend            | 4, 6      |
| R-04 | Workflow retries duplicate an external action.                   | Medium     | High   | Idempotency keys, deduplication records, connector capability metadata, compensating actions, and operator review.                    | Automation         | 11        |
| R-05 | Provider outage or quota failure blocks work.                    | High       | Medium | Health-aware routing, timeouts, circuit breakers, user-visible degradation, budgets, and fallback where policy permits.               | AI Platform        | 9         |
| R-06 | Browser/desktop executor compromises host or secrets.            | Medium     | High   | Ephemeral isolation, network egress policy, no host mounts by default, artifact sanitization, and approval gates.                     | Platform Security  | 13, 14    |
| R-07 | Privacy obligations conflict with audit retention.               | Medium     | High   | Data classification, retention matrix, pseudonymized audit references, legal hold design, and deletion workflows.                     | Privacy            | 1, 4      |
| R-08 | Workflow complexity causes unreliable or opaque behavior.        | Medium     | Medium | Versioning, validation, deterministic state machine, replay-safe logs, templates, and clear run diagnostics.                          | Product/Automation | 11, 12    |
| R-09 | Operating cost grows unpredictably with model or automation use. | High       | Medium | Per-workspace budgets, token/tool metering, limits, alerts, caching where safe, and pricing telemetry.                                | Platform           | 9, 22     |
| R-10 | Accessibility gaps exclude users.                                | Medium     | Medium | WCAG acceptance tests, keyboard-first components, semantic review, and assistive-technology QA.                                       | Frontend           | 7, 23     |

## Risk governance

High-impact risks require a documented control and test before the related feature can leave beta. Risk status is reviewed at each milestone gate and after security incidents, material provider changes, or new executor capabilities.
