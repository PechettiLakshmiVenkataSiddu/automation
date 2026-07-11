"""Organization-scoped workflow draft and immutable-version persistence."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aether.workflows.definition import ValidatedDefinition


class SqlAlchemyWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        organization_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None,
        definition: ValidatedDefinition,
    ) -> UUID:
        workflow_id, version_id = uuid4(), uuid4()
        await self._session.execute(
            text("""
            INSERT INTO workflows (id, organization_id, created_by_user_id, name, description, status, current_version)
            VALUES (:id,:org,:user,:name,:description,'draft',1)
        """),
            {
                "id": workflow_id,
                "org": organization_id,
                "user": user_id,
                "name": name,
                "description": description,
            },
        )
        await self._version(organization_id, workflow_id, version_id, 1, user_id, definition)
        return workflow_id

    async def save_draft(
        self,
        organization_id: UUID,
        workflow_id: UUID,
        user_id: UUID,
        definition: ValidatedDefinition,
    ) -> int:
        version = (
            await self._session.execute(
                text("""
            UPDATE workflows SET current_version=current_version + 1, updated_at=now()
            WHERE id=:workflow_id AND organization_id=:org AND status='draft' RETURNING current_version
        """),
                {"workflow_id": workflow_id, "org": organization_id},
            )
        ).scalar_one_or_none()
        if version is None:
            raise ValueError("Draft workflow was not found")
        await self._version(
            organization_id, workflow_id, uuid4(), int(version), user_id, definition
        )
        return int(version)

    async def set_status(self, organization_id: UUID, workflow_id: UUID, status: str) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE workflows SET status=:status, updated_at=now()
            WHERE id=:workflow_id AND organization_id=:org
              AND ((:status='active' AND status='draft') OR (:status='archived' AND status IN ('draft','paused','active')) OR (:status='paused' AND status='active'))
        """),
            {"workflow_id": workflow_id, "org": organization_id, "status": status},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def list_workflows(self, organization_id: UUID) -> list[dict[str, object]]:
        result = await self._session.execute(
            text("""
            SELECT id,name,description,status,current_version,updated_at FROM workflows
            WHERE organization_id=:org ORDER BY updated_at DESC
        """),
            {"org": organization_id},
        )
        return [dict(row._mapping) for row in result]

    async def get(self, organization_id: UUID, workflow_id: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text("""
            SELECT w.id,w.name,w.description,w.status,w.current_version,v.definition,v.definition_hash,v.created_at
            FROM workflows w JOIN workflow_versions v ON v.workflow_id=w.id AND v.version=w.current_version
            WHERE w.id=:workflow_id AND w.organization_id=:org AND v.organization_id=:org
        """),
                    {"workflow_id": workflow_id, "org": organization_id},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def export(self, organization_id: UUID, workflow_id: UUID) -> dict[str, object] | None:
        item = await self.get(organization_id, workflow_id)
        if item is None:
            return None
        return {
            "format": "aether.workflow.v1",
            "name": item["name"],
            "description": item["description"],
            "definition": item["definition"],
        }

    async def list_schedules(
        self, organization_id: UUID, workflow_id: UUID
    ) -> list[dict[str, object]]:
        rows = await self._session.execute(
            text("""
            SELECT s.id,s.cron_expression,s.timezone,s.enabled,s.next_run_at,s.last_run_at
            FROM schedules s JOIN workflows w ON w.id=s.workflow_id
            WHERE s.organization_id=:org AND s.workflow_id=:workflow_id AND w.organization_id=:org
            ORDER BY s.created_at DESC
        """),
            {"org": organization_id, "workflow_id": workflow_id},
        )
        return [dict(row._mapping) for row in rows]

    async def create_schedule(
        self, organization_id: UUID, workflow_id: UUID, user_id: UUID, cron: str, timezone: str
    ) -> UUID:
        schedule_id = uuid4()
        result = await self._session.execute(
            text("""
            INSERT INTO schedules (id,organization_id,workflow_id,created_by_user_id,cron_expression,timezone)
            SELECT :id,:org,id,:user,:cron,:timezone FROM workflows
            WHERE id=:workflow_id AND organization_id=:org AND status IN ('draft','active','paused')
        """),
            {
                "id": schedule_id,
                "org": organization_id,
                "workflow_id": workflow_id,
                "user": user_id,
                "cron": cron,
                "timezone": timezone,
            },
        )
        if not result.rowcount:  # type: ignore[attr-defined]
            raise ValueError("Workflow is not available for scheduling")
        return schedule_id

    async def set_schedule_enabled(
        self, organization_id: UUID, workflow_id: UUID, schedule_id: UUID, enabled: bool
    ) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE schedules SET enabled=:enabled,updated_at=now()
            WHERE id=:schedule_id AND workflow_id=:workflow_id AND organization_id=:org
        """),
            {
                "schedule_id": schedule_id,
                "workflow_id": workflow_id,
                "org": organization_id,
                "enabled": enabled,
            },
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def delete_schedule(
        self, organization_id: UUID, workflow_id: UUID, schedule_id: UUID
    ) -> bool:
        result = await self._session.execute(
            text(
                "DELETE FROM schedules WHERE id=:schedule_id AND workflow_id=:workflow_id AND organization_id=:org"
            ),
            {"schedule_id": schedule_id, "workflow_id": workflow_id, "org": organization_id},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def _version(
        self,
        org: UUID,
        workflow_id: UUID,
        version_id: UUID,
        version: int,
        user: UUID,
        definition: ValidatedDefinition,
    ) -> None:
        await self._session.execute(
            text("""
            INSERT INTO workflow_versions (id,organization_id,workflow_id,version,definition,definition_hash,created_by_user_id)
            VALUES (:id,:org,:workflow_id,:version,CAST(:definition AS jsonb),:hash,:user)
        """),
            {
                "id": version_id,
                "org": org,
                "workflow_id": workflow_id,
                "version": version,
                "definition": json.dumps(definition.value),
                "hash": definition.definition_hash,
                "user": user,
            },
        )
