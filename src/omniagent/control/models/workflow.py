"""Workflow domain models."""

from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class NodeType(str, Enum):
    TASK = "task"
    HITL = "hitl"
    PARALLEL = "parallel"
    DECISION = "decision"


class Node(OmniBaseModel):
    id: str
    node_type: NodeType
    action: str | None = None
    adapter_id: str | None = None
    timeout_seconds: int = 60
    rollback_handler: str | None = None
    config: dict = Field(default_factory=dict)


class Edge(OmniBaseModel):
    from_node: str
    to_node: str
    condition: str | None = None


class StateGraph(OmniBaseModel):
    nodes: list[Node]
    edges: list[Edge]
    start_node: str
    end_nodes: list[str]


class WorkflowDefinition(EntityModel):
    name: str
    version: str
    description: str = ""
    graph: StateGraph
    config: dict = Field(default_factory=dict)


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class WorkflowExecution(EntityModel):
    workflow_id: UUID
    status: ExecutionStatus = ExecutionStatus.PENDING
    current_node: str | None = None
    context: dict = Field(default_factory=dict)
    error: str | None = None


class WorkflowCreate(OmniBaseModel):
    name: str
    version: str
    description: str = ""
    graph: StateGraph
    config: dict = Field(default_factory=dict)
