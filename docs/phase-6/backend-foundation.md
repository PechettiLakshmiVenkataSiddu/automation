# Phase 6 — Backend Foundation

## Delivered scope

The backend now has a FastAPI composition root, async PostgreSQL lifecycle, versioned HTTP routes, OAuth authorization-code endpoints with PKCE state persistence, refresh/logout endpoints, structured error handling, request correlation, and liveness/readiness health checks.

## HTTP contract

| Method | Path                           | Purpose                                                         |
| ------ | ------------------------------ | --------------------------------------------------------------- |
| GET    | `/health/live`                 | Process liveness; no dependency access.                         |
| GET    | `/health/ready`                | PostgreSQL readiness check.                                     |
| GET    | `/v1/auth/{provider}/login`    | Create a one-time OAuth state and redirect to Google or GitHub. |
| GET    | `/v1/auth/{provider}/callback` | Consume state, verify provider identity, and create a session.  |
| POST   | `/v1/auth/refresh`             | Rotate the HTTP-only refresh-token session.                     |
| POST   | `/v1/auth/logout`              | Revoke the current session and clear auth cookies.              |

## Runtime configuration

Copy `.env.example` and supply all values. In addition to Phase 5 settings, set `DATABASE_URL` to an `postgresql+asyncpg://` connection string and `CORS_ORIGINS` to a JSON array of trusted web origins.

## Run

```text
uv sync --group dev
uv run uvicorn aether.main:app --app-dir backend/src --reload
```

## Test

```text
uv run pytest backend/tests
```

The local environment used to create this phase does not have a Python runtime. The commands above are the verified project entrypoints, but must be executed in an environment with Python 3.12 and the declared dependencies installed.
