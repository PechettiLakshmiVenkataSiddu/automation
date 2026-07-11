"""PostgreSQL authority for isolated browser tasks and redacted artifacts."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyBrowserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_task(
        self, org: UUID, user: UUID, allowed_hosts: tuple[str, ...], credential_ref: UUID | None
    ) -> UUID:
        task_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO browser_tasks (id,organization_id,requested_by_user_id,status,allowed_hosts,credential_reference,expires_at)
            VALUES (:id,:org,:user,'queued',CAST(:hosts AS jsonb),:credential,now() + interval '10 minutes')
        """),
            {
                "id": task_id,
                "org": org,
                "user": user,
                "hosts": json.dumps(list(allowed_hosts)),
                "credential": credential_ref,
            },
        )
        return task_id

    async def cancel(self, org: UUID, task_id: UUID) -> bool:
        result = await self._session.execute(
            text("""
            UPDATE browser_tasks SET cancellation_requested_at=now(),status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END,updated_at=now()
            WHERE id=:task_id AND organization_id=:org AND status NOT IN ('succeeded','failed','cancelled')
        """),
            {"task_id": task_id, "org": org},
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def get_task(self, org: UUID, task_id: UUID) -> dict[str, object] | None:
        row = (
            (
                await self._session.execute(
                    text(
                        "SELECT id,status,allowed_hosts,credential_reference,cancellation_requested_at,expires_at FROM browser_tasks WHERE id=:task_id AND organization_id=:org"
                    ),
                    {"task_id": task_id, "org": org},
                )
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row else None

    async def add_artifact(
        self, org: UUID, task_id: UUID, artifact_type: str, object_key: str, sha256: str
    ) -> UUID:
        artifact_id = uuid4()
        await self._session.execute(
            text("""
            INSERT INTO browser_task_artifacts (id,organization_id,browser_task_id,artifact_type,object_key,sha256,redacted)
            SELECT :id,:org,id,:type,:key,:sha,true FROM browser_tasks WHERE id=:task_id AND organization_id=:org
        """),
            {
                "id": artifact_id,
                "org": org,
                "task_id": task_id,
                "type": artifact_type,
                "key": object_key,
                "sha": sha256,
            },
        )
        return artifact_id
