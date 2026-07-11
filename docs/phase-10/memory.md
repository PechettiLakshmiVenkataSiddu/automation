# Phase 10 — User-controlled long-term memory

Memory is disabled by default for each organization/user pair. A user must explicitly enable memory before creating it; withdrawing consent immediately excludes every memory from chat retrieval. Every API query scopes both `organization_id` and the authenticated `user_id`.

## API

- `PUT` / `GET` `/v1/memories/consent`
- `POST`, `GET`, `DELETE` `/v1/memories`
- `PATCH`, `DELETE` `/v1/memories/{memory_id}`
- `GET /v1/memories/export`

Deletion is a user-requested soft deletion, preserving only minimal operational metadata. The migration adds consent records, retention/provenance lifecycle columns, and deletion-request records. Apply `database/schema/0004_memory_governance.sql` after the existing three migrations.

## Chat boundary

Chat retrieves at most eight opt-in, non-expired memories and at most 3,000 characters total. It sends them to the model as quoted reference data under a system instruction that they are not executable instructions. The chat response returns the memory identifiers/text used so a user can remove a source directly.

## UI

`/memory` provides consent, create, list, individual delete, and confirmation-gated forget-all controls. Export is available through the authenticated API for portable user data.
