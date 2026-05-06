"""Learning loop — real feedback extraction and strategy optimization (Req 15)."""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.intelligence.algorithms.optimization import (
    compute_deviation,
    exponential_moving_average,
    nelder_mead,
)
from omniagent.intelligence.models.learning import AdjustmentStatus, LearningAdjustment
from omniagent.settings import LearningLoopSettings

logger = logging.getLogger(__name__)


class LearningLoopService(BaseService):
    def __init__(self, settings: LearningLoopSettings) -> None:
        super().__init__()
        self._settings = settings
        self._adjustments: dict[str, LearningAdjustment] = {}
        self._history: dict[str, list[dict]] = {}

    def record_execution_result(self, strategy_id: str, metrics: dict) -> None:
        self._history.setdefault(strategy_id, []).append(metrics)
        if len(self._history[strategy_id]) > 1000:
            self._history[strategy_id] = self._history[strategy_id][-1000:]

    async def analyze_strategy(self, strategy_id: UUID, expected_metrics: dict) -> LearningAdjustment | None:
        history = self._history.get(str(strategy_id), [])
        if len(history) < 10:
            return None

        deviations = self._compute_deviations(history, expected_metrics)
        if not deviations:
            return None

        max_deviation = max(deviations.values())
        if max_deviation < self._settings.auto_apply_threshold:
            return None

        current_params = expected_metrics
        suggested_params = self._optimize_params(history, expected_metrics)

        adjustment = LearningAdjustment(
            id=uuid4(),
            strategy_id=strategy_id,
            trigger_reason=(
                f"Metrics deviate by {max_deviation:.1%} "
                f"(threshold: {self._settings.auto_apply_threshold:.1%}). "
                f"Deviating metrics: {', '.join(k for k, v in deviations.items() if v >= self._settings.auto_apply_threshold)}"
            ),
            current_params=current_params,
            suggested_params=suggested_params,
            expected_improvement={"deviation_reduction": max_deviation * 0.5, "deviations": deviations},
        )
        self._adjustments[str(adjustment.id)] = adjustment
        logger.info(f"Learning adjustment generated: {adjustment.id}, deviation={max_deviation:.1%}")
        return adjustment

    async def approve_adjustment(self, adjustment_id: str, approver: str) -> LearningAdjustment:
        adj = self._adjustments.get(adjustment_id)
        if adj is None:
            raise ValueError(f"Adjustment not found: {adjustment_id}")
        adj.status = AdjustmentStatus.APPROVED
        adj.approved_by = approver
        return adj

    async def apply_adjustment(self, adjustment_id: str) -> LearningAdjustment:
        adj = self._adjustments.get(adjustment_id)
        if adj is None:
            raise ValueError(f"Adjustment not found: {adjustment_id}")
        if adj.status == AdjustmentStatus.PENDING and self._settings.mode != "auto":
            raise ValueError("Auto-apply disabled; adjustment must be approved first")
        adj.status = AdjustmentStatus.APPLIED
        adj.applied_at = datetime.utcnow()
        logger.info(f"Adjustment applied: {adjustment_id}")
        return adj

    async def reject_adjustment(self, adjustment_id: str) -> LearningAdjustment:
        adj = self._adjustments.get(adjustment_id)
        if adj is None:
            raise ValueError(f"Adjustment not found: {adjustment_id}")
        adj.status = AdjustmentStatus.REJECTED
        return adj

    def list_adjustments(self, status: AdjustmentStatus | None = None) -> list[LearningAdjustment]:
        if status is None:
            return list(self._adjustments.values())
        return [a for a in self._adjustments.values() if a.status == status]

    def _compute_deviations(self, history: list[dict], expected: dict) -> dict[str, float]:
        deviations = {}
        for metric_name, expected_value in expected.items():
            if not isinstance(expected_value, (int, float)) or expected_value == 0:
                continue
            actual_values = [h.get(metric_name) for h in history if isinstance(h.get(metric_name), (int, float))]
            if len(actual_values) < 5:
                continue
            smoothed = exponential_moving_average(actual_values, alpha=0.3)
            recent = smoothed[-5:]
            avg_recent = sum(recent) / len(recent)
            deviation = abs(avg_recent - expected_value) / abs(expected_value)
            deviations[metric_name] = deviation
        return deviations

    def _optimize_params(self, history: list[dict], current_params: dict) -> dict:
        numeric_params = {k: v for k, v in current_params.items() if isinstance(v, (int, float))}
        if not numeric_params:
            return current_params

        param_names = list(numeric_params.keys())
        param_values = [float(numeric_params[k]) for k in param_names]

        def objective(params: list[float]) -> float:
            total_error = 0.0
            for i, name in enumerate(param_names):
                actual_vals = [h.get(name) for h in history[-20:] if isinstance(h.get(name), (int, float))]
                if actual_vals:
                    avg_actual = sum(actual_vals) / len(actual_vals)
                    total_error += (avg_actual - params[i]) ** 2
            return total_error

        optimized, _ = nelder_mead(objective, param_values, max_iter=100)

        result = dict(current_params)
        for i, name in enumerate(param_names):
            result[name] = round(optimized[i], 4)
        return result
