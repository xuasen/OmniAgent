"""Rollback handler chain (Req 5)."""

import logging

from omniagent.control.models.workflow import Node, StateGraph

logger = logging.getLogger(__name__)


class RollbackHandler:
    async def rollback_nodes(self, completed_nodes: list[str], graph: StateGraph, context: dict) -> list[str]:
        """Execute rollback handlers in reverse order for completed nodes."""
        node_map = {n.id: n for n in graph.nodes}
        rolled_back: list[str] = []

        for node_id in reversed(completed_nodes):
            node = node_map.get(node_id)
            if node is None:
                continue
            if node.rollback_handler:
                try:
                    await self._execute_rollback(node, context)
                    rolled_back.append(node_id)
                    logger.info(f"Rolled back node: {node_id}")
                except Exception as e:
                    logger.error(f"Rollback failed for node {node_id}: {e}")
                    break

        return rolled_back

    async def _execute_rollback(self, node: Node, context: dict) -> None:
        # Stub: execute the rollback handler action
        logger.info(f"Executing rollback handler for node {node.id}: {node.rollback_handler}")
