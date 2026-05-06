"""Strategy domain models."""

from enum import Enum
from uuid import UUID

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class ObjectiveDirection(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class Objective(OmniBaseModel):
    metric: str
    direction: ObjectiveDirection
    priority: int = 1
    weight: float = 1.0


class Constraint(OmniBaseModel):
    metric: str
    operator: str  # "<", ">", "<=", ">=", "=="
    value: float | str
    hard: bool = True


class StrategyDefinition(EntityModel):
    name: str
    version: str
    objectives: list[Objective]
    constraints: list[Constraint] = Field(default_factory=list)
    decision_graph_id: UUID | None = None
    config: dict = Field(default_factory=dict)
    active: bool = True


class ThompsonArmState(OmniBaseModel):
    arm_id: str
    alpha: float = 1.0
    beta: float = 1.0
    total_pulls: int = 0
    expected_value: float = 0.5


class EvaluationMode(str, Enum):
    PARETO = "pareto"
    THOMPSON = "thompson"
    WEIGHTED = "weighted"


class StrategyDecision(EntityModel):
    strategy_id: UUID
    execution_id: UUID | None = None
    chosen_path: dict
    candidates: list[dict]
    reasoning: str
    metrics: dict = Field(default_factory=dict)
    evaluation_mode: EvaluationMode = EvaluationMode.PARETO
    pareto_frontier_size: int = 0
