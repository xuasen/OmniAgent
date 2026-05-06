"""Unit tests for FinOps service."""

import pytest
from uuid import uuid4

from omniagent.common.events import EventBus
from omniagent.intelligence.models.finops import CostTier, ModelRoute, RoutingRule
from omniagent.intelligence.services.finops import FinOpsService
from omniagent.settings import FinOpsSettings


@pytest.fixture
def finops():
    service = FinOpsService(settings=FinOpsSettings(), event_bus=EventBus())
    service.load_routes([
        ModelRoute(
            id=uuid4(), model_id="gpt-4", endpoint="http://api/gpt4",
            cost_tier=CostTier.PREMIUM, cost_per_1k_tokens=0.03,
            max_latency_ms=5000, priority=0,
        ),
        ModelRoute(
            id=uuid4(), model_id="gpt-3.5", endpoint="http://api/gpt35",
            cost_tier=CostTier.STANDARD, cost_per_1k_tokens=0.002,
            max_latency_ms=2000, priority=1,
        ),
        ModelRoute(
            id=uuid4(), model_id="small-model", endpoint="http://api/small",
            cost_tier=CostTier.ECONOMY, cost_per_1k_tokens=0.0005,
            max_latency_ms=1000, priority=2,
        ),
    ])
    service.load_routing_rules([
        RoutingRule(name="premium", conditions={"user_tier": "premium"}, target_cost_tier=CostTier.PREMIUM),
        RoutingRule(name="default", conditions={}, target_cost_tier=CostTier.STANDARD),
    ])
    return service


@pytest.mark.unit
async def test_route_premium_user(finops):
    route = await finops.route_request({"user_tier": "premium"})
    assert route.cost_tier == CostTier.PREMIUM
    assert route.model_id == "gpt-4"


@pytest.mark.unit
async def test_route_default_user(finops):
    route = await finops.route_request({"user_tier": "free"})
    assert route.cost_tier == CostTier.STANDARD


@pytest.mark.unit
async def test_downgrade_on_cost_exceeded(finops):
    await finops.record_cost("exec-1", "gpt-4", 6.0)
    downgraded = await finops.check_and_downgrade("exec-1", cost_limit=5.0)
    assert downgraded is not None
    assert downgraded.cost_tier == CostTier.ECONOMY


@pytest.mark.unit
async def test_no_downgrade_under_limit(finops):
    await finops.record_cost("exec-2", "gpt-4", 1.0)
    downgraded = await finops.check_and_downgrade("exec-2", cost_limit=5.0)
    assert downgraded is None
