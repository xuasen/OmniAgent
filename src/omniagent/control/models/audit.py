"""Audit domain models."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class AuditEntry(EntityModel):
    execution_id: UUID | None = None
    node_id: str | None = None
    event_type: str
    actor: str
    actor_type: str  # "agent" or "human"
    decision_basis: str | None = None
    details: dict = Field(default_factory=dict)


class AuditQuery(OmniBaseModel):
    execution_id: UUID | None = None
    event_type: str | None = None
    actor: str | None = None
    time_start: datetime | None = None
    time_end: datetime | None = None
    offset: int = 0
    limit: int = 50
