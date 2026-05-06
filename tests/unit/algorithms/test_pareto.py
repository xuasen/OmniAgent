"""Tests for Pareto frontier algorithm."""

import pytest

from omniagent.intelligence.algorithms.pareto import (
    Objective,
    compute_pareto_frontier,
    dominates,
    select_from_frontier,
)


@pytest.mark.unit
def test_dominates_simple():
    objs = [Objective("cost", "minimize"), Objective("quality", "maximize")]
    a = {"cost": 10, "quality": 90}
    b = {"cost": 20, "quality": 80}
    assert dominates(a, b, objs) is True
    assert dominates(b, a, objs) is False


@pytest.mark.unit
def test_no_domination_tradeoff():
    objs = [Objective("cost", "minimize"), Objective("quality", "maximize")]
    a = {"cost": 10, "quality": 70}  # cheaper but lower quality
    b = {"cost": 20, "quality": 90}  # expensive but higher quality
    assert dominates(a, b, objs) is False
    assert dominates(b, a, objs) is False


@pytest.mark.unit
def test_pareto_frontier():
    objs = [Objective("cost", "minimize"), Objective("quality", "maximize")]
    candidates = [
        {"name": "A", "cost": 10, "quality": 90},   # on frontier
        {"name": "B", "cost": 20, "quality": 80},   # dominated by A
        {"name": "C", "cost": 5, "quality": 60},    # on frontier (cheapest)
        {"name": "D", "cost": 15, "quality": 95},   # on frontier
    ]
    frontier = compute_pareto_frontier(candidates, objs)
    names = {c["name"] for c in frontier}
    assert "B" not in names
    assert "A" in names
    assert "C" in names
    assert "D" in names


@pytest.mark.unit
def test_select_from_frontier():
    objs = [
        Objective("cost", "minimize", weight=1.0),
        Objective("quality", "maximize", weight=2.0),
    ]
    frontier = [
        {"name": "cheap", "cost": 5, "quality": 60},
        {"name": "balanced", "cost": 10, "quality": 90},
        {"name": "premium", "cost": 15, "quality": 95},
    ]
    selected = select_from_frontier(frontier, objs)
    # With quality weighted 2x, should prefer higher quality
    assert selected is not None
    assert selected["name"] in ("balanced", "premium")


@pytest.mark.unit
def test_empty_frontier():
    assert select_from_frontier([], []) is None


@pytest.mark.unit
def test_single_item_frontier():
    objs = [Objective("x", "maximize")]
    result = select_from_frontier([{"x": 42}], objs)
    assert result == {"x": 42}
