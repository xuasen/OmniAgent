"""Checkpoint persistence for workflow recovery (Req 5)."""

import logging
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from omniagent.db.models.workflow import CheckpointModel

logger = logging.getLogger(__name__)


class CheckpointService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_checkpoint(self, execution_id: UUID, node_id: str, state: dict) -> UUID:
        checkpoint = CheckpointModel(
            id=uuid4(),
            execution_id=execution_id,
            node_id=node_id,
            state=state,
        )
        self._session.add(checkpoint)
        await self._session.flush()
        logger.info(f"Checkpoint saved: execution={execution_id}, node={node_id}")
        return checkpoint.id

    async def get_latest_checkpoint(self, execution_id: UUID) -> dict | None:
        from sqlalchemy import select, desc

        stmt = (
            select(CheckpointModel)
            .where(CheckpointModel.execution_id == execution_id)
            .order_by(desc(CheckpointModel.created_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return {"node_id": model.node_id, "state": model.state, "created_at": model.created_at}
