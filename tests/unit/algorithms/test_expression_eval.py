"""Tests for expression evaluator."""

import pytest

from omniagent.intelligence.algorithms.expression_eval import evaluate_expression


@pytest.mark.unit
def test_simple_equality():
    assert evaluate_expression("x == 1", {"x": 1}) is True
    assert evaluate_expression("x == 2", {"x": 1}) is False


@pytest.mark.unit
def test_string_comparison():
    assert evaluate_expression("name == 'alice'", {"name": "alice"}) is True
    assert evaluate_expression("name != 'bob'", {"name": "alice"}) is True


@pytest.mark.unit
def test_numeric_comparison():
    assert evaluate_expression("cost < 100", {"cost": 50}) is True
    assert evaluate_expression("cost >= 100", {"cost": 100}) is True
    assert evaluate_expression("cost > 100", {"cost": 100}) is False


@pytest.mark.unit
def test_nested_path():
    variables = {"request": {"model": "gpt-4", "tokens": 500}}
    assert evaluate_expression("request.model == 'gpt-4'", variables) is True
    assert evaluate_expression("request.tokens > 100", variables) is True


@pytest.mark.unit
def test_and_operator():
    variables = {"cost": 50, "quality": 90}
    assert evaluate_expression("cost < 100 && quality > 80", variables) is True
    assert evaluate_expression("cost < 100 && quality > 95", variables) is False


@pytest.mark.unit
def test_or_operator():
    variables = {"tier": "free"}
    assert evaluate_expression("tier == 'premium' || tier == 'free'", variables) is True
    assert evaluate_expression("tier == 'premium' || tier == 'enterprise'", variables) is False


@pytest.mark.unit
def test_in_operator():
    variables = {"tier": "premium"}
    assert evaluate_expression("tier in ['premium', 'enterprise']", variables) is True
    assert evaluate_expression("tier in ['free', 'basic']", variables) is False


@pytest.mark.unit
def test_contains_operator():
    variables = {"model": "gpt-4-turbo"}
    assert evaluate_expression("model contains 'gpt-4'", variables) is True
    assert evaluate_expression("model contains 'claude'", variables) is False


@pytest.mark.unit
def test_empty_expression():
    assert evaluate_expression("", {}) is True


@pytest.mark.unit
def test_boolean_values():
    assert evaluate_expression("active == true", {"active": True}) is True
    assert evaluate_expression("active == false", {"active": False}) is True
