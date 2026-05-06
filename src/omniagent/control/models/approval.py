"""HITL approval domain models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ApprovalRequest(EntityModel):
    execution_id: UUID
    node_id: str
    context_summary: dict = Field(default_factory=dict)
    escalation_level: int = 1
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_id: str | None = None
    decision_reason: str | None = None
    timeout_at: datetime | None = None
    decided_at: datetime | None = None


class ApprovalDecision(OmniBaseModel):
    decision: str  # "approve" or "reject"
    reason: str = ""
    approver_id: str = ""
