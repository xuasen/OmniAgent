"""Conflict resolution domain models."""

from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class ConflictRecord(EntityModel):
    execution_id: UUID | None = None
    conflicting_agents: list[str]
    conflict_type: str
    agent_decisions: list[dict]
    arbitration_rule: str | None = None
    resolution: dict = Field(default_factory=dict)
    escalated: bool = False


class ArbitrationRule(OmniBaseModel):
    name: str
    method: str  # "priority", "weight", "constraint"
    config: dict = Field(default_factory=dict)
