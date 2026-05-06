"""Learning loop domain models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class AdjustmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"


class LearningAdjustment(EntityModel):
    strategy_id: UUID
    status: AdjustmentStatus = AdjustmentStatus.PENDING
    trigger_reason: str
    current_params: dict
    suggested_params: dict
    expected_improvement: dict
    actual_improvement: dict | None = None
    approved_by: str | None = None
    applied_at: datetime | None = None
