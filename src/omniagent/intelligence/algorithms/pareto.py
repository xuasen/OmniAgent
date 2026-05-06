"""Pareto frontier computation and selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Objective:
    metric: str
    direction: str  # "maximize" or "minimize"
    weight: float = 1.0


def dominates(a: dict[str, Any], b: dict[str, Any], objectives: list[Objective]) -> bool:
    at_least_one_strict = False
    for obj in objectives:
        val_a = a.get(obj.metric, 0)
        val_b = b.get(obj.metric, 0)
        if not isinstance(val_a, (int, float)) or not isinstance(val_b, (int, float)):
            continue
        if obj.direction == "minimize":
            val_a, val_b = -val_a, -val_b
        if val_a < val_b:
            return False
        if val_a > val_b:
            at_least_one_strict = True
    return at_least_one_strict


def compute_pareto_frontier(candidates: list[dict], objectives: list[Objective]) -> list[dict]:
    frontier = []
    for i, c in enumerate(candidates):
        is_dominated = False
        for j, other in enumerate(candidates):
            if i == j:
                continue
            if dominates(other, c, objectives):
                is_dominated = True
                break
        if not is_dominated:
            frontier.append(c)
    return frontier


def select_from_frontier(frontier: list[dict], objectives: list[Objective]) -> dict | None:
    """Select best from frontier using weighted Chebyshev scalarization (min max regret)."""
    if not frontier:
        return None
    if len(frontier) == 1:
        return frontier[0]

    ideal: dict[str, float] = {}
    nadir: dict[str, float] = {}

    for obj in objectives:
        values = [c.get(obj.metric, 0) for c in frontier if isinstance(c.get(obj.metric, 0), (int, float))]
        if not values:
            continue
        if obj.direction == "maximize":
            ideal[obj.metric] = max(values)
            nadir[obj.metric] = min(values)
        else:
            ideal[obj.metric] = min(values)
            nadir[obj.metric] = max(values)

    best_candidate = None
    best_score = float("inf")

    for c in frontier:
        max_distance = 0.0
        for obj in objectives:
            val = c.get(obj.metric, 0)
            if not isinstance(val, (int, float)):
                continue
            span = abs(ideal.get(obj.metric, 0) - nadir.get(obj.metric, 0))
            if span == 0:
                continue
            if obj.direction == "maximize":
                distance = (ideal[obj.metric] - val) / span
            else:
                distance = (val - ideal[obj.metric]) / span
            max_distance = max(max_distance, distance * obj.weight)

        if max_distance < best_score:
            best_score = max_distance
            best_candidate = c

    return best_candidate
