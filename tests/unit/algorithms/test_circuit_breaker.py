"""Tests for circuit breaker."""

import time

import pytest

from omniagent.intelligence.algorithms.circuit_breaker import CircuitBreaker, CircuitState


@pytest.mark.unit
def test_initial_state():
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True


@pytest.mark.unit
def test_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False


@pytest.mark.unit
def test_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.01)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.02)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN


@pytest.mark.unit
def test_half_open_to_closed():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.01, half_open_max_calls=2)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.02)
    cb.can_execute()
    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.unit
def test_half_open_to_open_on_failure():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.01)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.02)
    cb.can_execute()
    assert cb.state == CircuitState.HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


@pytest.mark.unit
def test_success_reduces_failure_count():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    assert cb.failure_count == 1  # Decremented by success
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED  # Still below threshold


@pytest.mark.unit
def test_reset():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
