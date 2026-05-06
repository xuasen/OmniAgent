"""Tests for Thompson Sampling."""

import pytest

from omniagent.intelligence.algorithms.thompson import ThompsonBandit


@pytest.mark.unit
def test_register_and_select():
    bandit = ThompsonBandit()
    bandit.register_arm("arm_a")
    bandit.register_arm("arm_b")
    selected = bandit.select_arm()
    assert selected in ("arm_a", "arm_b")


@pytest.mark.unit
def test_empty_bandit():
    bandit = ThompsonBandit()
    assert bandit.select_arm() is None


@pytest.mark.unit
def test_update_favors_winner():
    bandit = ThompsonBandit()
    bandit.register_arm("good")
    bandit.register_arm("bad")
    for _ in range(100):
        bandit.update("good", 1.0)
        bandit.update("bad", 0.0)
    ev = bandit.get_expected_values()
    assert ev["good"] > ev["bad"]


@pytest.mark.unit
def test_arm_state():
    bandit = ThompsonBandit()
    bandit.register_arm("test", prior_alpha=5.0, prior_beta=2.0)
    state = bandit.get_state("test")
    assert state is not None
    assert state.alpha == 5.0
    assert state.expected_value == pytest.approx(5.0 / 7.0, abs=0.01)


@pytest.mark.unit
def test_remove_arm():
    bandit = ThompsonBandit()
    bandit.register_arm("x")
    bandit.remove_arm("x")
    assert bandit.arm_count == 0
