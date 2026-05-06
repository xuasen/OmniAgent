"""Trace store service — persistence and retrieval (Req 2)."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from omniagent.common.base_service import BaseService
from omniagent.db.models.trace import TraceModel
from omniagent.exceptions import TraceStoreError, ResourceNotFoundError
from omniagent.common.trace import Trace, TraceQuery, TraceStatus
from omniagent.settings import TraceStoreSettings

logger = logging.getLogger(__name__)

MAX_TRACE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class TraceStoreService(BaseService):
    def __init__(self, session: AsyncSession, settings: TraceStoreSettings) -> None:
        super().__init__()
        self._session = session
        self._settings = settings

    async def save(self, trace: Trace) -> Trace:
        import json
        serialized = json.dumps(trace.model_dump(mode="json"))
        if len(serialized.encode()) > MAX_TRACE_SIZE_BYTES:
            raise TraceStoreError(
                f"Trace {trace.id} exceeds max size",
                details={"trace_id": str(trace.id), "size_bytes": len(serialized.encode())},
            )

        expires_at = datetime.utcnow() + timedelta(days=self._settings.retention_days)
        model = TraceModel(
            id=trace.id,
            agent_id=trace.agent_id,
            adapter_id=trace.adapter_id,
            status=trace.status.value if isinstance(trace.status, TraceStatus) else trace.status,
            steps=trace.model_dump(mode="json")["steps"],
            total_duration_ms=trace.total_duration_ms,
            total_tokens=trace.total_tokens,
            total_cost_usd=trace.total_cost_usd,
            metadata_=trace.metadata,
            source_trace_id=trace.source_trace_id,
            created_at=trace.created_at,
            updated_at=trace.updated_at,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return trace

    async def get(self, trace_id: UUID) -> Trace:
        model = await self._session.get(TraceModel, trace_id)
        if model is None:
            raise ResourceNotFoundError(f"Trace not found: {trace_id}")
        return self._to_domain(model)

    async def query(self, query: TraceQuery) -> list[Trace]:
        stmt = select(TraceModel)
        conditions = []

        if query.agent_id:
            conditions.append(TraceModel.agent_id == query.agent_id)
        if query.adapter_id:
            conditions.append(TraceModel.adapter_id == query.adapter_id)
        if query.status:
            conditions.append(TraceModel.status == query.status.value)
        if query.time_start:
            conditions.append(TraceModel.created_at >= query.time_start)
        if query.time_end:
            conditions.append(TraceModel.created_at <= query.time_end)
        if query.min_cost is not None:
            conditions.append(TraceModel.total_cost_usd >= query.min_cost)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(TraceModel.created_at))
        stmt = stmt.offset(query.offset).limit(min(query.limit, self._settings.max_query_limit))

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def delete_expired(self) -> int:
        from sqlalchemy import delete as sql_delete

        stmt = sql_delete(TraceModel).where(
            TraceModel.expires_at <= datetime.utcnow()
        )
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    def _to_domain(self, model: TraceModel) -> Trace:
        return Trace(
            id=model.id,
            agent_id=model.agent_id,
            adapter_id=model.adapter_id,
            status=TraceStatus(model.status),
            steps=model.steps,
            total_duration_ms=model.total_duration_ms,
            total_tokens=model.total_tokens,
            total_cost_usd=float(model.total_cost_usd) if model.total_cost_usd else None,
            metadata=model.metadata_,
            source_trace_id=model.source_trace_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            expires_at=model.expires_at,
        )
