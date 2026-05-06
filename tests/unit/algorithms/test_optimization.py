"""Tests for optimization algorithms."""

import pytest

from omniagent.intelligence.algorithms.optimization import (
    compute_deviation,
    exponential_moving_average,
    nelder_mead,
)


@pytest.mark.unit
def test_nelder_mead_quadratic():
    # Minimize (x-3)^2 + (y-4)^2
    def f(params):
        return (params[0] - 3) ** 2 + (params[1] - 4) ** 2

    result, value = nelder_mead(f, [0.0, 0.0], max_iter=500)
    assert abs(result[0] - 3.0) < 0.1
    assert abs(result[1] - 4.0) < 0.1
    assert value < 0.01


@pytest.mark.unit
def test_nelder_mead_rosenbrock():
    # Classic test: Rosenbrock function minimum at (1, 1)
    def rosenbrock(params):
        x, y = params
        return (1 - x) ** 2 + 100 * (y - x**2) ** 2

    result, value = nelder_mead(rosenbrock, [0.0, 0.0], max_iter=1000)
    assert abs(result[0] - 1.0) < 0.5
    assert abs(result[1] - 1.0) < 0.5


@pytest.mark.unit
def test_ema_basic():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    ema = exponential_moving_average(values, alpha=0.5)
    assert len(ema) == 5
    assert ema[0] == 10.0
    # EMA should be between min and max
    assert all(10.0 <= v <= 50.0 for v in ema)
    # Should be monotonically increasing for increasing input
    assert all(ema[i] <= ema[i + 1] for i in range(len(ema) - 1))


@pytest.mark.unit
def test_ema_empty():
    assert exponential_moving_average([]) == []


@pytest.mark.unit
def test_ema_single():
    assert exponential_moving_average([42.0]) == [42.0]


@pytest.mark.unit
def test_compute_deviation():
    actual = [1.2, 2.4, 3.6]
    expected = [1.0, 2.0, 3.0]
    dev = compute_deviation(actual, expected)
    assert dev is not None
    assert abs(dev - 0.2) < 0.01  # 20% average deviation


@pytest.mark.unit
def test_compute_deviation_zero_expected():
    actual = [1.0, 2.0]
    expected = [0.0, 2.0]
    dev = compute_deviation(actual, expected)
    # Should skip zero-expected values
    assert dev is not None


@pytest.mark.unit
def test_compute_deviation_mismatched():
    assert compute_deviation([1.0], [1.0, 2.0]) is None
    assert compute_deviation([], []) is None
