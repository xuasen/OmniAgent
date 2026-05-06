"""Unit tests for ExperimentEngineService."""

import pytest
from uuid import uuid4

from omniagent.common.events import EventBus
from omniagent.intelligence.models.experiment import (
    ExperimentCreate,
    ExperimentStatus,
    Variant,
)
from omniagent.intelligence.services.experiment_engine import ExperimentEngineService
from omniagent.settings import ExperimentEngineSettings


@pytest.fixture
def engine():
    return ExperimentEngineService(settings=ExperimentEngineSettings(), event_bus=EventBus())


@pytest.fixture
def create_request():
    return ExperimentCreate(
        name="test-experiment",
        variants=[
            Variant(id="A", strategy_id=uuid4(), traffic_percentage=50),
            Variant(id="B", strategy_id=uuid4(), traffic_percentage=50),
        ],
        target_sample_size=1000,
    )


@pytest.mark.unit
async def test_create_experiment(engine, create_request):
    exp = await engine.create_experiment(create_request)
    assert exp.name == "test-experiment"
    assert exp.status == ExperimentStatus.DRAFT
    assert len(exp.variants) == 2


@pytest.mark.unit
async def test_start_experiment(engine, create_request):
    exp = await engine.create_experiment(create_request)
    started = await engine.start_experiment(str(exp.id))
    assert started.status == ExperimentStatus.RUNNING
    assert started.started_at is not None


@pytest.mark.unit
async def test_route_request(engine, create_request):
    exp = await engine.create_experiment(create_request)
    await engine.start_experiment(str(exp.id))
    variant = engine.route_request(str(exp.id))
    assert variant in ("A", "B")


@pytest.mark.unit
async def test_invalid_traffic_split(engine):
    with pytest.raises(ValueError, match="sum to 100"):
        await engine.create_experiment(ExperimentCreate(
            name="bad",
            variants=[
                Variant(id="A", strategy_id=uuid4(), traffic_percentage=30),
                Variant(id="B", strategy_id=uuid4(), traffic_percentage=30),
            ],
        ))
