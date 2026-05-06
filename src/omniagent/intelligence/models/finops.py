"""AI FinOps domain models."""

from enum import Enum

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class CostTier(str, Enum):
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"


class ModelRoute(EntityModel):
    model_id: str
    endpoint: str
    cost_tier: CostTier
    cost_per_1k_tokens: float
    max_latency_ms: int
    capabilities: list[str] = Field(default_factory=list)
    priority: int = 0
    enabled: bool = True


class RoutingRule(OmniBaseModel):
    name: str
    conditions: dict = Field(default_factory=dict)
    target_cost_tier: CostTier
    max_cost_usd: float | None = None


class CostSummary(OmniBaseModel):
    total_cost_usd: float = 0.0
    by_model: dict[str, float] = Field(default_factory=dict)
    by_workflow: dict[str, float] = Field(default_factory=dict)
    downgrade_count: int = 0
