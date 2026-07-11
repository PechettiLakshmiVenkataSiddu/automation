# Technology Decisions

| Area              | Selected technology                           | Rationale                                                                | Constraints                                                                         |
| ----------------- | --------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Web application   | Next.js 15, React, TypeScript                 | Server-rendering, mature ecosystem, and a typed component model.         | Pin supported versions and maintain browser compatibility policy.                   |
| UI                | Tailwind CSS, shadcn/ui                       | Accessible composable primitives and controlled design-system ownership. | Components must pass accessibility and visual regression tests.                     |
| Client state/data | TanStack Query, Zustand                       | Separate server cache from local UI state.                               | No sensitive tokens in browser state.                                               |
| API               | FastAPI, Pydantic                             | Typed async Python APIs with OpenAPI generation.                         | API contract changes require versioning policy.                                     |
| Persistence       | PostgreSQL, SQLAlchemy, Alembic               | Strong transactions, mature migrations, and relational integrity.        | Migrations must be backward-compatible for rolling deployments.                     |
| Background work   | Celery, Redis, APScheduler                    | Mature task execution and scheduling suitable for phased delivery.       | Authoritative status remains in PostgreSQL.                                         |
| Vector retrieval  | ChromaDB                                      | Supports initial knowledge-base retrieval workload.                      | No source-of-truth user data exists only in the vector store.                       |
| AI providers      | OpenAI, Anthropic, Gemini, Ollama             | Balances managed capability with local deployment options.               | Requests must pass the model gateway and data policy.                               |
| Automation        | Playwright, MCP, constrained Python execution | Covers browser, tools, and extensible agent capabilities.                | Executors run outside the API process and are policy gated.                         |
| Voice             | Whisper, Piper                                | Speech-to-text and local-capable text-to-speech options.                 | Audio retention follows explicit user policy.                                       |
| Deployment        | Docker, Docker Compose, Nginx                 | Repeatable local and initial production topology.                        | Production secrets and TLS are externally managed.                                  |
| Delivery          | GitHub Actions                                | Widely supported CI/CD integration.                                      | Protected branches, signed artifacts, and least-privilege credentials are required. |

## Explicit deferrals

- Kubernetes is deferred until deployment scale and reliability requirements justify its operational cost.
- Microservices are deferred under ADR-001.
- Native mobile clients are outside the initial release boundary; the web application must remain responsive.
- Payments and marketplace revenue flows are outside the initial release until a business model and compliance scope are approved.
