"""Experiment domain models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class Variant(OmniBaseModel):
    id: str
    strategy_id: UUID
    traffic_percentage: float


class Experiment(EntityModel):
    name: str
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: list[Variant]
    target_sample_size: int | None = None
    target_duration_hours: int | None = None
    safety_thresholds: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    report: dict | None = None


class ExperimentCreate(OmniBaseModel):
    name: str
    variants: list[Variant]
    target_sample_size: int | None = None
    target_duration_hours: int | None = None
    safety_thresholds: dict = Field(default_factory=dict)


class ExperimentReport(OmniBaseModel):
    experiment_id: UUID
    variants: list[dict]
    winner: str | None = None
    statistical_significance: float | None = None
    total_samples: int = 0
