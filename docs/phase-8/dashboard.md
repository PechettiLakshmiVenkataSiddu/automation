# Phase 8 — Dashboard

The dashboard provides a live organization-scoped operational overview. It resolves the authenticated user's active organization, then shows workflow totals by state, outstanding approvals, and the five most recent runs. All values are read from PostgreSQL; no dashboard data is fabricated in the client.

## API

- `GET /v1/me/organizations` returns organizations available to the authenticated user.
- `GET /v1/dashboard/summary?organization_id={uuid}` returns the validated organization summary.

The API verifies the access-token signature, checks that its backing session has not been revoked, and confirms active membership before returning organization data.
