"""Node execution dispatcher (Req 5)."""

import asyncio
import logging
from datetime import datetime

from omniagent.common.events import Event, EventBus
from omniagent.control.models.workflow import Node, NodeType

logger = logging.getLogger(__name__)


class NodeExecutor:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def execute_node(self, node: Node, context: dict) -> dict:
        logger.info(f"Executing node: {node.id} (type={node.node_type})")

        if node.node_type == NodeType.HITL:
            return {"status": "paused", "reason": "awaiting_approval"}

        try:
            result = await asyncio.wait_for(
                self._dispatch(node, context),
                timeout=node.timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.error(f"Node {node.id} timed out after {node.timeout_seconds}s")
            raise

        await self._event_bus.publish(Event(
            event_type="node.completed",
            payload={"node_id": node.id, "result": result},
            source="executor",
        ))
        return result

    async def _dispatch(self, node: Node, context: dict) -> dict:
        # Stub: dispatch to appropriate adapter based on node config
        return {"node_id": node.id, "status": "completed", "timestamp": datetime.utcnow().isoformat()}
