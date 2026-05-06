"""Experiment engine — A/B testing with statistical significance and auto-stop (Req 14)."""

import logging
import random
from datetime import datetime
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.intelligence.algorithms.statistics import (
    chi_squared_test,
    sequential_test,
    welch_t_test,
)
from omniagent.intelligence.models.experiment import (
    Experiment,
    ExperimentCreate,
    ExperimentReport,
    ExperimentStatus,
    Variant,
)
from omniagent.settings import ExperimentEngineSettings

logger = logging.getLogger(__name__)


class ExperimentEngineService(BaseService):
    def __init__(self, settings: ExperimentEngineSettings, event_bus: EventBus) -> None:
        super().__init__()
        self._settings = settings
        self._event_bus = event_bus
        self._experiments: dict[str, Experiment] = {}
        self._metrics: dict[str, dict[str, list[dict]]] = {}

    async def create_experiment(self, create: ExperimentCreate) -> Experiment:
        total_traffic = sum(v.traffic_percentage for v in create.variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Traffic percentages must sum to 100, got {total_traffic}")

        experiment = Experiment(
            id=uuid4(),
            name=create.name,
            variants=create.variants,
            target_sample_size=create.target_sample_size,
            target_duration_hours=create.target_duration_hours,
            safety_thresholds=create.safety_thresholds,
        )
        self._experiments[str(experiment.id)] = experiment
        self._metrics[str(experiment.id)] = {v.id: [] for v in create.variants}
        return experiment

    async def start_experiment(self, experiment_id: str) -> Experiment:
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment not found: {experiment_id}")
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.utcnow()

        await self._event_bus.publish(Event(
            event_type="experiment.started",
            payload={"experiment_id": experiment_id, "name": exp.name},
            source="experiment_engine",
        ))
        return exp

    async def stop_experiment(self, experiment_id: str) -> Experiment:
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment not found: {experiment_id}")
        exp.status = ExperimentStatus.STOPPED
        exp.completed_at = datetime.utcnow()
        return exp

    def route_request(self, experiment_id: str) -> str | None:
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status != ExperimentStatus.RUNNING:
            return None

        roll = random.uniform(0, 100)
        cumulative = 0.0
        for variant in exp.variants:
            cumulative += variant.traffic_percentage
            if roll <= cumulative:
                return variant.id
        return exp.variants[-1].id if exp.variants else None

    async def record_metric(self, experiment_id: str, variant_id: str, metrics: dict) -> None:
        exp_metrics = self._metrics.get(experiment_id)
        if exp_metrics is None:
            return
        variant_metrics = exp_metrics.get(variant_id)
        if variant_metrics is not None:
            variant_metrics.append(metrics)

        await self._check_safety(experiment_id, variant_id, metrics)

    async def _check_safety(self, experiment_id: str, variant_id: str, metrics: dict) -> None:
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status != ExperimentStatus.RUNNING:
            return
        for metric_name, threshold in exp.safety_thresholds.items():
            if metric_name in metrics and metrics[metric_name] > threshold:
                variant_data = self._metrics.get(experiment_id, {}).get(variant_id, [])
                violations = sum(1 for m in variant_data if m.get(metric_name, 0) > threshold)
                violation_rate = violations / len(variant_data) if variant_data else 0
                if violation_rate > 0.1:  # > 10% violation rate
                    logger.warning(f"Safety threshold breached: exp={experiment_id}, variant={variant_id}, metric={metric_name}")
                    await self._event_bus.publish(Event(
                        event_type="experiment.safety_breach",
                        payload={"experiment_id": experiment_id, "variant_id": variant_id, "metric": metric_name},
                        source="experiment_engine",
                    ))

    async def check_significance(self, experiment_id: str, metric_name: str = "success") -> dict:
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment not found: {experiment_id}")
        if len(exp.variants) < 2:
            return {"significant": False, "reason": "need at least 2 variants"}

        metrics_a = self._metrics.get(experiment_id, {}).get(exp.variants[0].id, [])
        metrics_b = self._metrics.get(experiment_id, {}).get(exp.variants[1].id, [])

        if not metrics_a or not metrics_b:
            return {"significant": False, "reason": "insufficient data"}

        # Check if metric is binary (success/failure) or continuous
        sample_val = metrics_a[0].get(metric_name, 0)
        if isinstance(sample_val, bool) or sample_val in (0, 1):
            successes_a = sum(1 for m in metrics_a if m.get(metric_name))
            successes_b = sum(1 for m in metrics_b if m.get(metric_name))
            result = chi_squared_test(successes_a, len(metrics_a), successes_b, len(metrics_b))
            return {
                "test": "chi_squared",
                "significant": result.significant,
                "p_value": result.p_value,
                "statistic": result.statistic,
                "confidence": result.confidence_level,
                "variant_a_rate": successes_a / len(metrics_a),
                "variant_b_rate": successes_b / len(metrics_b),
            }
        else:
            import statistics as std_stats
            vals_a = [m.get(metric_name, 0) for m in metrics_a]
            vals_b = [m.get(metric_name, 0) for m in metrics_b]
            mean_a, mean_b = std_stats.mean(vals_a), std_stats.mean(vals_b)
            std_a = std_stats.stdev(vals_a) if len(vals_a) > 1 else 0
            std_b = std_stats.stdev(vals_b) if len(vals_b) > 1 else 0
            result = welch_t_test(mean_a, std_a, len(vals_a), mean_b, std_b, len(vals_b))
            return {
                "test": "welch_t",
                "significant": result.significant,
                "p_value": result.p_value,
                "statistic": result.statistic,
                "confidence": result.confidence_level,
                "variant_a_mean": mean_a,
                "variant_b_mean": mean_b,
            }

    async def check_sequential(self, experiment_id: str, metric_name: str = "success") -> str:
        """Run SPRT to check if experiment can stop early. Returns 'continue'/'accept_h1'/'reject_h1'."""
        exp = self._experiments.get(experiment_id)
        if exp is None or len(exp.variants) < 2:
            return "continue"

        metrics_b = self._metrics.get(experiment_id, {}).get(exp.variants[1].id, [])
        if not metrics_b:
            return "continue"

        successes = sum(1 for m in metrics_b if m.get(metric_name))
        failures = len(metrics_b) - successes

        # H0: variant B same as baseline, H1: variant B is 10% better
        baseline_metrics = self._metrics.get(experiment_id, {}).get(exp.variants[0].id, [])
        if not baseline_metrics:
            return "continue"
        p0 = sum(1 for m in baseline_metrics if m.get(metric_name)) / len(baseline_metrics)
        p1 = min(p0 + 0.1, 0.99)

        return sequential_test(successes, failures, p0=p0, p1=p1)

    async def generate_report(self, experiment_id: str) -> ExperimentReport:
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment not found: {experiment_id}")

        variant_results = []
        for variant in exp.variants:
            metrics = self._metrics.get(experiment_id, {}).get(variant.id, [])
            variant_results.append({
                "variant_id": variant.id,
                "sample_count": len(metrics),
                "metrics_summary": self._summarize_metrics(metrics),
            })

        total_samples = sum(r["sample_count"] for r in variant_results)

        winner = None
        if len(variant_results) >= 2 and total_samples > 0:
            sig = await self.check_significance(experiment_id)
            if sig.get("significant"):
                rate_a = sig.get("variant_a_rate") or sig.get("variant_a_mean", 0)
                rate_b = sig.get("variant_b_rate") or sig.get("variant_b_mean", 0)
                winner = exp.variants[0].id if rate_a > rate_b else exp.variants[1].id

        return ExperimentReport(
            experiment_id=exp.id,
            variants=variant_results,
            winner=winner,
            statistical_significance=sig.get("p_value") if total_samples > 0 and len(variant_results) >= 2 else None,
            total_samples=total_samples,
        )

    def _summarize_metrics(self, metrics: list[dict]) -> dict:
        if not metrics:
            return {}
        summary: dict[str, dict] = {}
        for m in metrics:
            for key, val in m.items():
                if isinstance(val, (int, float)):
                    if key not in summary:
                        summary[key] = {"sum": 0, "count": 0, "min": val, "max": val}
                    summary[key]["sum"] += val
                    summary[key]["count"] += 1
                    summary[key]["min"] = min(summary[key]["min"], val)
                    summary[key]["max"] = max(summary[key]["max"], val)
        return {k: {"mean": v["sum"] / v["count"], "min": v["min"], "max": v["max"], "count": v["count"]}
                for k, v in summary.items()}
