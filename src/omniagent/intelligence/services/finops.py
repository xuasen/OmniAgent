"""AI FinOps — model routing with circuit breaker, sliding window budget, predictive cost (Req 17)."""

import logging
import time
from collections import defaultdict
from uuid import uuid4

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.exceptions import OmniAgentError
from omniagent.intelligence.algorithms.circuit_breaker import CircuitBreaker, CircuitState
from omniagent.intelligence.models.finops import CostSummary, CostTier, ModelRoute, RoutingRule
from omniagent.settings import FinOpsSettings

logger = logging.getLogger(__name__)


class FinOpsService(BaseService):
    def __init__(self, settings: FinOpsSettings, event_bus: EventBus) -> None:
        super().__init__()
        self._settings = settings
        self._event_bus = event_bus
        self._routes: list[ModelRoute] = []
        self._routing_rules: list[RoutingRule] = []
        self._cumulative_cost: dict[str, float] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._sliding_window: dict[str, list[tuple[float, float]]] = defaultdict(list)  # model_id -> [(timestamp, cost)]
        self._model_latencies: dict[str, list[float]] = defaultdict(list)

    def load_routes(self, routes: list[ModelRoute]) -> None:
        self._routes = routes
        for route in routes:
            if route.model_id not in self._circuit_breakers:
                self._circuit_breakers[route.model_id] = CircuitBreaker(
                    failure_threshold=5,
                    recovery_timeout_s=self._settings.failover_timeout_seconds,
                )
        logger.info(f"Loaded {len(routes)} model routes with circuit breakers")

    def load_routing_rules(self, rules: list[RoutingRule]) -> None:
        self._routing_rules = rules

    async def route_request(self, context: dict) -> ModelRoute:
        target_tier = self._determine_tier(context)
        available = self._get_healthy_routes(target_tier)

        if not available:
            available = self._get_healthy_routes(None)

        if not available:
            raise OmniAgentError(
                "No available model endpoints",
                details={"context": context, "reason": "all_circuits_open"},
            )

        return available[0]

    async def route_with_failover(self, context: dict) -> ModelRoute:
        target_tier = self._determine_tier(context)
        candidates = self._get_healthy_routes(target_tier)
        if not candidates:
            candidates = self._get_healthy_routes(None)
        if not candidates:
            raise OmniAgentError("All model endpoints unavailable")
        return candidates[0]

    def record_success(self, model_id: str, latency_ms: float) -> None:
        cb = self._circuit_breakers.get(model_id)
        if cb:
            cb.record_success()
        self._model_latencies[model_id].append(latency_ms)
        if len(self._model_latencies[model_id]) > 100:
            self._model_latencies[model_id] = self._model_latencies[model_id][-100:]

    def record_failure(self, model_id: str) -> None:
        cb = self._circuit_breakers.get(model_id)
        if cb:
            cb.record_failure()
            if cb.state == CircuitState.OPEN:
                logger.warning(f"Circuit breaker OPEN for model: {model_id}")

    async def record_cost(self, execution_id: str, model_id: str, cost_usd: float) -> None:
        self._cumulative_cost[execution_id] = self._cumulative_cost.get(execution_id, 0) + cost_usd
        self._sliding_window[model_id].append((time.time(), cost_usd))
        # Trim to 1-hour window
        cutoff = time.time() - 3600
        self._sliding_window[model_id] = [
            (t, c) for t, c in self._sliding_window[model_id] if t > cutoff
        ]

    async def check_and_downgrade(self, execution_id: str, cost_limit: float) -> ModelRoute | None:
        current_cost = self._cumulative_cost.get(execution_id, 0)
        if current_cost < cost_limit:
            return None

        economy_routes = self._get_healthy_routes(CostTier.ECONOMY)
        if not economy_routes:
            return None

        downgraded = economy_routes[0]
        await self._event_bus.publish(Event(
            event_type="finops.downgrade",
            payload={
                "execution_id": execution_id,
                "new_model": downgraded.model_id,
                "current_cost": current_cost,
                "cost_limit": cost_limit,
            },
            source="finops",
        ))
        return downgraded

    def predict_cost(self, model_id: str, estimated_tokens: int) -> float:
        route = next((r for r in self._routes if r.model_id == model_id), None)
        if route is None:
            return 0.0
        return route.cost_per_1k_tokens * estimated_tokens / 1000

    def get_model_health(self) -> dict[str, dict]:
        health = {}
        for model_id, cb in self._circuit_breakers.items():
            latencies = self._model_latencies.get(model_id, [])
            health[model_id] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
                "hourly_cost": sum(c for _, c in self._sliding_window.get(model_id, [])),
            }
        return health

    def get_cost_summary(self) -> CostSummary:
        total = sum(self._cumulative_cost.values())
        by_model: dict[str, float] = {}
        for model_id, records in self._sliding_window.items():
            by_model[model_id] = sum(c for _, c in records)
        downgrade_count = 0  # Would be tracked from events
        return CostSummary(total_cost_usd=total, by_model=by_model, downgrade_count=downgrade_count)

    def _get_healthy_routes(self, tier: CostTier | None) -> list[ModelRoute]:
        routes = []
        for r in self._routes:
            if not r.enabled:
                continue
            if tier is not None and r.cost_tier != tier:
                continue
            cb = self._circuit_breakers.get(r.model_id)
            if cb and not cb.can_execute():
                continue
            routes.append(r)
        routes.sort(key=lambda r: r.priority)
        return routes

    def _determine_tier(self, context: dict) -> CostTier:
        for rule in self._routing_rules:
            if not rule.conditions:
                return rule.target_cost_tier
            matches = all(context.get(k) == v for k, v in rule.conditions.items())
            if matches:
                return rule.target_cost_tier
        return CostTier.STANDARD
