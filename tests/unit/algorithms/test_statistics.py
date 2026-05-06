"""Tests for statistical algorithms."""

import pytest

from omniagent.intelligence.algorithms.statistics import (
    chi_squared_test,
    sequential_test,
    welch_t_test,
)


@pytest.mark.unit
def test_chi_squared_significant_difference():
    # A: 80/100 success, B: 60/100 success — should be significant
    result = chi_squared_test(80, 100, 60, 100, alpha=0.05)
    assert result.significant is True
    assert result.p_value < 0.05


@pytest.mark.unit
def test_chi_squared_no_difference():
    # A: 50/100, B: 52/100 — not significant
    result = chi_squared_test(50, 100, 52, 100, alpha=0.05)
    assert result.significant is False


@pytest.mark.unit
def test_chi_squared_empty_sample():
    result = chi_squared_test(0, 0, 0, 0)
    assert result.significant is False
    assert result.p_value == 1.0


@pytest.mark.unit
def test_welch_t_test_significant():
    # Very different means with low variance
    result = welch_t_test(mean_a=10.0, std_a=1.0, n_a=50, mean_b=8.0, std_b=1.0, n_b=50)
    assert result.significant is True


@pytest.mark.unit
def test_welch_t_test_not_significant():
    # Similar means with high variance
    result = welch_t_test(mean_a=10.0, std_a=5.0, n_a=10, mean_b=9.5, std_b=5.0, n_b=10)
    assert result.significant is False


@pytest.mark.unit
def test_welch_t_test_small_sample():
    result = welch_t_test(mean_a=10.0, std_a=1.0, n_a=1, mean_b=5.0, std_b=1.0, n_b=1)
    assert result.significant is False  # Too small for significance


@pytest.mark.unit
def test_sequential_test_continue():
    result = sequential_test(successes=5, failures=5, p0=0.5, p1=0.6)
    assert result == "continue"


@pytest.mark.unit
def test_sequential_test_accept():
    # Overwhelming evidence for H1
    result = sequential_test(successes=50, failures=5, p0=0.5, p1=0.7)
    assert result == "accept_h1"


@pytest.mark.unit
def test_sequential_test_reject():
    # Overwhelming evidence against H1
    result = sequential_test(successes=5, failures=50, p0=0.5, p1=0.7)
    assert result == "reject_h1"
