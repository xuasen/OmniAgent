"""Observability and audit service (Req 7)."""

import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.control.models.audit import AuditEntry, AuditQuery
from omniagent.db.models.audit import AuditLogModel

logger = logging.getLogger(__name__)


class ObservabilityService(BaseService):
    def __init__(self, session: AsyncSession, event_bus: EventBus, audit_retry_max: int = 3) -> None:
        super().__init__()
        self._session = session
        self._event_bus = event_bus
        self._audit_retry_max = audit_retry_max

    async def start(self) -> None:
        await super().start()
        self._event_bus.subscribe("workflow.started", self._on_workflow_event)
        self._event_bus.subscribe("workflow.rolled_back", self._on_workflow_event)
        self._event_bus.subscribe("node.completed", self._on_workflow_event)
        self._event_bus.subscribe("hitl.decision_made", self._on_workflow_event)

    async def emit_audit_log(self, entry: AuditEntry) -> None:
        model = AuditLogModel(
            id=entry.id,
            execution_id=entry.execution_id,
            node_id=entry.node_id,
            event_type=entry.event_type,
            actor=entry.actor,
            actor_type=entry.actor_type,
            decision_basis=entry.decision_basis,
            details=entry.details,
            created_at=entry.created_at,
        )
        for attempt in range(self._audit_retry_max):
            try:
                self._session.add(model)
                await self._session.flush()
                return
            except Exception as e:
                if attempt == self._audit_retry_max - 1:
                    logger.critical(f"Audit log write failed after {self._audit_retry_max} retries: {e}")
                    raise
                logger.warning(f"Audit log write retry {attempt + 1}: {e}")

    async def query_audit_logs(self, query: AuditQuery) -> list[AuditEntry]:
        stmt = select(AuditLogModel)
        conditions = []

        if query.execution_id:
            conditions.append(AuditLogModel.execution_id == query.execution_id)
        if query.event_type:
            conditions.append(AuditLogModel.event_type == query.event_type)
        if query.actor:
            conditions.append(AuditLogModel.actor == query.actor)
        if query.time_start:
            conditions.append(AuditLogModel.created_at >= query.time_start)
        if query.time_end:
            conditions.append(AuditLogModel.created_at <= query.time_end)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(AuditLogModel.created_at))
        stmt = stmt.offset(query.offset).limit(query.limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def export_jsonlines(self, query: AuditQuery) -> str:
        entries = await self.query_audit_logs(query)
        lines = [json.dumps(e.model_dump(mode="json")) for e in entries]
        return "\n".join(lines)

    async def _on_workflow_event(self, event: Event) -> None:
        entry = AuditEntry(
            id=uuid4(),
            event_type=event.event_type,
            actor=event.source,
            actor_type="agent",
            details=event.payload,
        )
        await self.emit_audit_log(entry)

    def _to_domain(self, model: AuditLogModel) -> AuditEntry:
        return AuditEntry(
            id=model.id,
            execution_id=model.execution_id,
            node_id=model.node_id,
            event_type=model.event_type,
            actor=model.actor,
            actor_type=model.actor_type,
            decision_basis=model.decision_basis,
            details=model.details,
            created_at=model.created_at,
        )
