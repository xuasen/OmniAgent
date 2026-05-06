"""Trace domain models."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class StepType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"


class TraceStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class TraceStep(OmniBaseModel):
    step_seq: int
    step_type: StepType
    content: str
    model_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    latency_ms: int | None = None
    tokens_used: int | None = None
    timestamp: datetime


class Trace(EntityModel):
    agent_id: str
    adapter_id: str
    status: TraceStatus = TraceStatus.RUNNING
    steps: list[TraceStep] = Field(default_factory=list)
    total_duration_ms: int | None = None
    total_tokens: int | None = None
    total_cost_usd: float | None = None
    metadata: dict = Field(default_factory=dict)
    source_trace_id: UUID | None = None
    expires_at: datetime | None = None


class TraceQuery(OmniBaseModel):
    agent_id: str | None = None
    adapter_id: str | None = None
    status: TraceStatus | None = None
    time_start: datetime | None = None
    time_end: datetime | None = None
    min_cost: float | None = None
    offset: int = 0
    limit: int = 50


class TraceCreate(OmniBaseModel):
    agent_id: str
    adapter_id: str
    metadata: dict = Field(default_factory=dict)


class TraceFinalize(OmniBaseModel):
    status: TraceStatus
    total_duration_ms: int
    total_tokens: int
    total_cost_usd: float
