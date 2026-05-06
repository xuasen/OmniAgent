"""Unit tests for StrategyEngineService."""

import pytest
from uuid import uuid4

from omniagent.exceptions import ValidationError
from omniagent.intelligence.models.strategy import (
    Constraint,
    Objective,
    ObjectiveDirection,
    StrategyDefinition,
)
from omniagent.intelligence.services.strategy_engine import StrategyEngineService
from omniagent.settings import StrategyEngineSettings


@pytest.fixture
def engine():
    return StrategyEngineService(settings=StrategyEngineSettings())


@pytest.fixture
def strategy():
    return StrategyDefinition(
        id=uuid4(),
        name="test-strategy",
        version="1.0",
        objectives=[
            Objective(metric="ROI", direction=ObjectiveDirection.MAXIMIZE, priority=2, weight=1.0),
            Objective(metric="cost", direction=ObjectiveDirection.MINIMIZE, priority=1, weight=0.8),
        ],
        constraints=[
            Constraint(metric="cost", operator="<", value=5000, hard=True),
        ],
    )


@pytest.mark.unit
def test_register_strategy(engine, strategy):
    engine.register_strategy(strategy)


@pytest.mark.unit
def test_register_invalid_strategy(engine):
    invalid = StrategyDefinition(
        id=uuid4(), name="bad", version="1.0", objectives=[]
    )
    with pytest.raises(ValidationError, match="at least one objective"):
        engine.register_strategy(invalid)


@pytest.mark.unit
async def test_evaluate(engine, strategy):
    engine.register_strategy(strategy)
    candidates = [
        {"ROI": 10, "cost": 3000, "name": "path_a"},
        {"ROI": 5, "cost": 1000, "name": "path_b"},
        {"ROI": 20, "cost": 6000, "name": "path_c"},  # violates cost constraint
    ]
    decision = await engine.evaluate(str(strategy.id), candidates)
    assert decision.chosen_path["name"] != "path_c"  # should not select infeasible path
