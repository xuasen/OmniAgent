"""Nash equilibrium and weighted voting for conflict resolution."""

from __future__ import annotations

from typing import Any


def nash_bargaining(
    agents: list[str],
    utilities: dict[str, dict[str, float]],
    disagreement_point: dict[str, float],
    resources: list[str],
) -> dict[str, str]:
    """
    Nash bargaining: assign each resource to the agent with highest surplus.
    Returns: {resource: winning_agent}
    """
    allocation: dict[str, str] = {}

    for resource in resources:
        best_agent = agents[0] if agents else ""
        best_surplus = -float("inf")
        for agent in agents:
            u = utilities.get(agent, {}).get(resource, 0)
            d = disagreement_point.get(agent, 0)
            surplus = u - d
            if surplus > best_surplus:
                best_surplus = surplus
                best_agent = agent
        allocation[resource] = best_agent

    return allocation


def weighted_voting(
    agent_decisions: dict[str, dict[str, Any]],
    weights: dict[str, float],
    history_penalty: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Weighted voting with fairness penalty for recent winners.
    Returns: {"winner": agent_id, "decision": decision, "scores": {...}}
    """
    if not agent_decisions:
        return {"winner": None, "decision": None, "scores": {}}

    penalties = history_penalty or {}
    scores: dict[str, float] = {}

    for agent, decision in agent_decisions.items():
        base_weight = weights.get(agent, 1.0)
        penalty = penalties.get(agent, 0.0)
        effective_weight = base_weight * (1.0 - min(penalty, 0.9))
        confidence = decision.get("confidence", 1.0) if isinstance(decision, dict) else 1.0
        scores[agent] = effective_weight * confidence

    winner = max(scores, key=lambda k: scores[k])
    return {
        "winner": winner,
        "decision": agent_decisions[winner],
        "method": "weighted_voting",
        "scores": scores,
    }


def update_fairness_penalty(
    history_penalty: dict[str, float],
    winner: str,
    decay: float = 0.1,
    increment: float = 0.2,
) -> dict[str, float]:
    """
    After a conflict resolution, increment winner's penalty and decay others'.
    """
    updated = {}
    for agent, penalty in history_penalty.items():
        if agent == winner:
            updated[agent] = min(penalty + increment, 0.9)
        else:
            updated[agent] = max(penalty - decay, 0.0)
    if winner not in updated:
        updated[winner] = increment
    return updated
