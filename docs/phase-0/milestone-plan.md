# Milestone Plan

## Delivery sequence

| Phase | Milestone                           | Primary outcome                                                      | Depends on | Exit gate                                                           |
| ----- | ----------------------------------- | -------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| 0     | Product Foundation                  | Approved vision, risks, decisions, and roadmap.                      | —          | Product and technical baseline approved.                            |
| 1     | Software Requirements Specification | Traceable system specification and API/domain requirements.          | 0          | Requirements are testable and prioritized.                          |
| 2     | System Architecture                 | Context, container, component, data-flow, and security architecture. | 1          | Architecture review approved.                                       |
| 3     | Repository Structure                | Monorepo layout, developer standards, tooling, and conventions.      | 2          | New contributor can bootstrap validation tools.                     |
| 4     | Database Design                     | Domain schema, migrations, retention model, and data contracts.      | 1, 2, 3    | Schema review and migration strategy approved.                      |
| 5–7   | Secure Platform Foundation          | Authentication, backend foundation, frontend foundation.             | 3, 4       | End-to-end authenticated vertical slice passes.                     |
| 8–10  | Core Intelligence                   | Dashboard, chat, and governed memory.                                | 5–7        | User can converse over authorized context.                          |
| 11–12 | Automation Core                     | Execution engine and workflow builder.                               | 5–10       | Approved workflow runs reliably with history.                       |
| 13–16 | Agentic Capabilities                | Browser, desktop, voice, and multi-agent system.                     | 11–12      | Isolated, policy-controlled agent execution passes security review. |
| 17–22 | Product Integrations and Operations | Developer tools, calendar, email, notifications, admin, analytics.   | 11–16      | Supported integrations meet operational acceptance tests.           |
| 23    | Quality Hardening                   | Full test strategy, performance, accessibility, security validation. | 5–22       | Release candidate meets quality thresholds.                         |
| 24–26 | Release Engineering                 | Docker, CI/CD, and deployment.                                       | 23         | Staged production deployment and rollback are proven.               |
| 27    | Documentation                       | Operations, security, API, user, and developer documentation.        | 1–26       | Documentation supports release readiness.                           |

## Critical path

Phase 0 → 1 → 2 → 3 → 4 → 5–7 → 8–10 → 11–12 → 13–16 → 23 → 24–26 → 27.

## Governance gates

1. **Architecture gate:** Approve phases 0–2 before repository and schema implementation.
2. **Security gate:** Threat model, authorization design, secret handling, and audit model must be approved before production-like integrations.
3. **Automation gate:** Idempotency, approval, executor isolation, and recovery designs must be accepted before external side effects.
4. **Release gate:** Security, accessibility, performance, disaster recovery, observability, and rollback evidence must pass before production deployment.
