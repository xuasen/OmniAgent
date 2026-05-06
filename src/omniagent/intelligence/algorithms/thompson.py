"""Thompson Sampling with Beta distribution for exploration/exploitation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class ArmState:
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def expected_value(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def total_pulls(self) -> int:
        return int(self.alpha + self.beta - 2)


class ThompsonBandit:
    def __init__(self) -> None:
        self._arms: dict[str, ArmState] = {}

    def register_arm(self, arm_id: str, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> None:
        self._arms[arm_id] = ArmState(alpha=prior_alpha, beta=prior_beta)

    def remove_arm(self, arm_id: str) -> None:
        self._arms.pop(arm_id, None)

    def select_arm(self) -> str | None:
        if not self._arms:
            return None
        best_arm = None
        best_sample = -1.0
        for arm_id, state in self._arms.items():
            sample = random.betavariate(state.alpha, state.beta)
            if sample > best_sample:
                best_sample = sample
                best_arm = arm_id
        return best_arm

    def update(self, arm_id: str, reward: float) -> None:
        """Update with reward in [0.0, 1.0]."""
        state = self._arms.get(arm_id)
        if state is None:
            return
        reward = max(0.0, min(1.0, reward))
        state.alpha += reward
        state.beta += (1.0 - reward)

    def get_state(self, arm_id: str) -> ArmState | None:
        return self._arms.get(arm_id)

    def get_expected_values(self) -> dict[str, float]:
        return {arm_id: state.expected_value for arm_id, state in self._arms.items()}

    @property
    def arm_count(self) -> int:
        return len(self._arms)
