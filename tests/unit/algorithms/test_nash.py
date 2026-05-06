"""Tests for Nash equilibrium and voting algorithms."""

import pytest

from omniagent.intelligence.algorithms.nash import (
    nash_bargaining,
    update_fairness_penalty,
    weighted_voting,
)


@pytest.mark.unit
def test_nash_bargaining_basic():
    agents = ["agent_a", "agent_b"]
    utilities = {
        "agent_a": {"slot_1": 10, "slot_2": 5},
        "agent_b": {"slot_1": 3, "slot_2": 8},
    }
    disagreement = {"agent_a": 0, "agent_b": 0}
    allocation = nash_bargaining(agents, utilities, disagreement, ["slot_1", "slot_2"])
    assert allocation["slot_1"] == "agent_a"  # Higher utility
    assert allocation["slot_2"] == "agent_b"  # Higher utility


@pytest.mark.unit
def test_nash_bargaining_with_disagreement():
    agents = ["a", "b"]
    utilities = {"a": {"r": 10}, "b": {"r": 8}}
    disagreement = {"a": 9, "b": 0}  # a has high disagreement point
    allocation = nash_bargaining(agents, utilities, disagreement, ["r"])
    # b has surplus 8, a has surplus 1 → b wins
    assert allocation["r"] == "b"


@pytest.mark.unit
def test_weighted_voting_basic():
    decisions = {
        "agent_a": {"action": "buy", "confidence": 0.9},
        "agent_b": {"action": "sell", "confidence": 0.8},
    }
    weights = {"agent_a": 2.0, "agent_b": 1.0}
    result = weighted_voting(decisions, weights)
    assert result["winner"] == "agent_a"
    assert result["method"] == "weighted_voting"


@pytest.mark.unit
def test_weighted_voting_with_penalty():
    decisions = {
        "agent_a": {"action": "buy", "confidence": 0.9},
        "agent_b": {"action": "sell", "confidence": 0.8},
    }
    weights = {"agent_a": 2.0, "agent_b": 2.0}
    # Heavy penalty on agent_a for winning too often
    penalty = {"agent_a": 0.8, "agent_b": 0.0}
    result = weighted_voting(decisions, weights, history_penalty=penalty)
    assert result["winner"] == "agent_b"


@pytest.mark.unit
def test_weighted_voting_empty():
    result = weighted_voting({}, {})
    assert result["winner"] is None


@pytest.mark.unit
def test_update_fairness_penalty():
    penalties = {"a": 0.3, "b": 0.1}
    updated = update_fairness_penalty(penalties, winner="a", decay=0.1, increment=0.2)
    assert updated["a"] == 0.5  # 0.3 + 0.2
    assert updated["b"] == 0.0  # 0.1 - 0.1


@pytest.mark.unit
def test_fairness_penalty_caps():
    penalties = {"a": 0.85}
    updated = update_fairness_penalty(penalties, winner="a", increment=0.2)
    assert updated["a"] == 0.9  # Capped at 0.9
