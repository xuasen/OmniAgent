"""Workflow orchestrator — DAG-based execution engine (Req 5)."""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.control.engine.dag import validate_dag, get_next_nodes, get_independent_nodes
from omniagent.control.engine.checkpoint import CheckpointService
from omniagent.control.engine.executor import NodeExecutor
from omniagent.control.engine.rollback import RollbackHandler
from omniagent.control.models.workflow import (
    ExecutionStatus,
    StateGraph,
    WorkflowDefinition,
    WorkflowExecution,
)
from omniagent.exceptions import WorkflowExecutionError, ValidationError
from omniagent.settings import OrchestratorSettings

logger = logging.getLogger(__name__)


class OrchestratorService(BaseService):
    def __init__(self, session: AsyncSession, settings: OrchestratorSettings, event_bus: EventBus) -> None:
        super().__init__()
        self._session = session
        self._settings = settings
        self._event_bus = event_bus
        self._checkpoint = CheckpointService(session)
        self._executor = NodeExecutor(event_bus)
        self._rollback = RollbackHandler()

    def validate_workflow(self, workflow: WorkflowDefinition) -> None:
        validate_dag(workflow.graph)

    async def start_execution(self, workflow: WorkflowDefinition, context: dict | None = None) -> WorkflowExecution:
        self.validate_workflow(workflow)

        execution = WorkflowExecution(
            id=uuid4(),
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            current_node=workflow.graph.start_node,
            context=context or {},
        )

        await self._event_bus.publish(Event(
            event_type="workflow.started",
            payload={"execution_id": str(execution.id), "workflow_id": str(workflow.id)},
            source="orchestrator",
        ))

        return execution

    async def execute_node(self, execution: WorkflowExecution, graph: StateGraph) -> dict:
        if execution.current_node is None:
            raise WorkflowExecutionError("No current node to execute")

        node_map = {n.id: n for n in graph.nodes}
        node = node_map.get(execution.current_node)
        if node is None:
            raise WorkflowExecutionError(f"Node not found: {execution.current_node}")

        result = await self._executor.execute_node(node, execution.context)

        if self._settings.checkpoint_enabled:
            await self._checkpoint.save_checkpoint(
                execution_id=execution.id,
                node_id=execution.current_node,
                state=execution.context,
            )

        return result

    async def advance(self, execution: WorkflowExecution, graph: StateGraph) -> ExecutionStatus:
        if execution.current_node in graph.end_nodes:
            execution.status = ExecutionStatus.COMPLETED
            return ExecutionStatus.COMPLETED

        next_nodes = get_next_nodes(graph, execution.current_node or "")
        if not next_nodes:
            execution.status = ExecutionStatus.COMPLETED
            return ExecutionStatus.COMPLETED

        execution.current_node = next_nodes[0]
        return ExecutionStatus.RUNNING

    async def rollback_execution(
        self, execution: WorkflowExecution, graph: StateGraph, completed_nodes: list[str]
    ) -> None:
        rolled_back = await self._rollback.rollback_nodes(completed_nodes, graph, execution.context)
        execution.status = ExecutionStatus.ROLLED_BACK

        await self._event_bus.publish(Event(
            event_type="workflow.rolled_back",
            payload={"execution_id": str(execution.id), "rolled_back_nodes": rolled_back},
            source="orchestrator",
        ))

    async def resume_from_checkpoint(self, execution_id: UUID) -> dict | None:
        return await self._checkpoint.get_latest_checkpoint(execution_id)
