"""Decision graph domain models."""

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class PathNode(OmniBaseModel):
    node_id: str
    action: str | None = None
    config: dict = Field(default_factory=dict)


class ExecutionPath(OmniBaseModel):
    id: str
    name: str
    nodes: list[PathNode]
    expected_cost: float | None = None
    expected_latency_ms: int | None = None
    conditions: dict = Field(default_factory=dict)


class DecisionGraph(EntityModel):
    name: str
    paths: list[ExecutionPath]
    fallback_paths: list[ExecutionPath] = Field(default_factory=list)
