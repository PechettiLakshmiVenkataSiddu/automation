# Phase 12 — Workflow Builder

Phase 12 introduces typed, versioned workflow definitions. A definition contains `nodes` and `edges`; node identifiers are unique, exactly one trigger is required, and every edge must reference an existing node. Supported nodes are trigger, action, condition, approval, and bounded loop nodes.

The backend validates the graph before a draft is versioned. Cycles are rejected unless their cycle includes a loop node with an explicit `max_iterations` between 1 and 100. Definitions are canonically hashed before persistence, preserving the Phase 4 immutable-version constraint.

Workflow commands and UI remain organization-scoped. An active workflow run always resolves a fixed version, never a mutable draft.

The `/workflows` editor starts with a manual trigger, exposes action, condition, approval, and loop nodes through keyboard-accessible buttons, and saves drafts through the authenticated workflow API. It never fabricates a persisted workflow in the browser.

Schedule controls use the existing `schedules` table and are scoped by both workflow and organization. The API supports schedule listing, creation, enable/disable, and deletion, plus portable workflow export/import and a safe approval template. Workflow run history exposes per-step diagnostics and pending approval data from PostgreSQL; approval decisions remain governed by the Phase 11 automation API.

The editor renders persisted schedules, run-step diagnostics, and pending approvals after a draft is saved. It uses the API to apply approval decisions, so the Phase 11 authorization and audit controls remain in effect.
