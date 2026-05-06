"""Conflict resolver — weighted voting + Nash + fairness tracking (Req 16)."""

import logging
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.intelligence.algorithms.nash import (
    nash_bargaining,
    update_fairness_penalty,
    weighted_voting,
)
from omniagent.intelligence.models.conflict import ArbitrationRule, ConflictRecord
from omniagent.settings import ConflictResolverSettings

logger = logging.getLogger(__name__)


class ConflictResolverService(BaseService):
    def __init__(self, settings: ConflictResolverSettings, event_bus: EventBus) -> None:
        super().__init__()
        self._settings = settings
        self._event_bus = event_bus
        self._rules: list[ArbitrationRule] = []
        self._records: dict[str, ConflictRecord] = {}
        self._agent_weights: dict[str, float] = {}
        self._fairness_penalties: dict[str, float] = {}

    def load_rules(self, rules: list[ArbitrationRule]) -> None:
        self._rules = rules
        logger.info(f"Loaded {len(rules)} arbitration rules")

    def set_agent_weights(self, weights: dict[str, float]) -> None:
        self._agent_weights = weights

    async def detect_and_resolve(
        self,
        execution_id: UUID | None,
        agent_decisions: dict[str, dict],
        resource: str,
    ) -> ConflictRecord:
        agents = list(agent_decisions.keys())
        if len(agents) < 2:
            raise ValueError("Conflict requires at least 2 agents")

        method = self._settings.default_arbitration
        resolution = self._arbitrate(agent_decisions, method, resource)
        escalated = self._should_escalate(agent_decisions)

        # Update fairness penalties
        winner = resolution.get("winner")
        if winner:
            self._fairness_penalties = update_fairness_penalty(
                self._fairness_penalties, winner
            )

        record = ConflictRecord(
            id=uuid4(),
            execution_id=execution_id,
            conflicting_agents=agents,
            conflict_type=f"resource_contention:{resource}",
            agent_decisions=[{"agent": a, "decision": d} for a, d in agent_decisions.items()],
            arbitration_rule=method,
            resolution=resolution,
            escalated=escalated,
        )
        self._records[str(record.id)] = record

        await self._event_bus.publish(Event(
            event_type="conflict.resolved",
            payload={
                "conflict_id": str(record.id),
                "agents": agents,
                "winner": winner,
                "method": method,
                "escalated": escalated,
            },
            source="conflict_resolver",
        ))

        return record

    def _arbitrate(self, agent_decisions: dict[str, dict], method: str, resource: str) -> dict:
        if method == "weighted_voting":
            return weighted_voting(
                agent_decisions,
                weights=self._agent_weights or {a: 1.0 for a in agent_decisions},
                history_penalty=self._fairness_penalties,
            )
        elif method == "nash":
            utilities = {
                agent: {resource: decision.get("utility", decision.get("priority", 0))}
                for agent, decision in agent_decisions.items()
            }
            disagreement = {agent: 0.0 for agent in agent_decisions}
            allocation = nash_bargaining(list(agent_decisions.keys()), utilities, disagreement, [resource])
            winner = allocation.get(resource, list(agent_decisions.keys())[0])
            return {"winner": winner, "decision": agent_decisions[winner], "method": "nash"}
        else:
            # Priority-based (default)
            prioritized = sorted(
                agent_decisions.items(),
                key=lambda x: x[1].get("priority", 0),
                reverse=True,
            )
            winner = prioritized[0]
            return {"winner": winner[0], "decision": winner[1], "method": "priority"}

    def _should_escalate(self, agent_decisions: dict[str, dict]) -> bool:
        if not self._settings.high_risk_escalation:
            return False
        for decision in agent_decisions.values():
            if decision.get("risk_level") == "high":
                return True
        return False

    def get_fairness_scores(self) -> dict[str, float]:
        return dict(self._fairness_penalties)

    def list_records(self) -> list[ConflictRecord]:
        return list(self._records.values())
