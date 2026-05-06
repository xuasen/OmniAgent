"""Replay domain models."""

from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class ReplayStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReplayOverrides(OmniBaseModel):
    model_id: str | None = None
    prompt_template: str | None = None
    agent_config: dict | None = None


class ReplaySession(EntityModel):
    source_trace_id: UUID
    overrides: ReplayOverrides
    status: ReplayStatus = ReplayStatus.PENDING
    result_trace_id: UUID | None = None


class ComparisonReport(OmniBaseModel):
    source_trace_id: UUID
    replay_trace_id: UUID
    status_match: bool
    duration_diff_ms: int | None = None
    tokens_diff: int | None = None
    cost_diff_usd: float | None = None
    step_diffs: list[dict] = Field(default_factory=list)


class BatchReplayRequest(OmniBaseModel):
    source_trace_ids: list[UUID]
    overrides: ReplayOverrides


class BatchReplayReport(OmniBaseModel):
    batch_id: UUID
    total_traces: int
    completed: int
    avg_cost_diff: float | None = None
    avg_latency_diff_ms: float | None = None
    result_match_rate: float | None = None
