"""Decision graph service — expression-based path selection with performance tracking (Req 12)."""

import logging
from collections import defaultdict

from omniagent.common.base_service import BaseService
from omniagent.intelligence.algorithms.expression_eval import evaluate_expression
from omniagent.intelligence.models.decision_graph import DecisionGraph, ExecutionPath
from omniagent.settings import DecisionGraphSettings

logger = logging.getLogger(__name__)


class PathPerformance:
    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._latencies: list[float] = []
        self._costs: list[float] = []
        self._successes: int = 0
        self._total: int = 0

    def record(self, latency_ms: float, cost: float, success: bool) -> None:
        self._latencies.append(latency_ms)
        self._costs.append(cost)
        self._total += 1
        if success:
            self._successes += 1
        if len(self._latencies) > self._window_size:
            self._latencies = self._latencies[-self._window_size:]
            self._costs = self._costs[-self._window_size:]

    @property
    def avg_latency_ms(self) -> float:
        return sum(self._latencies) / len(self._latencies) if self._latencies else 0

    @property
    def avg_cost(self) -> float:
        return sum(self._costs) / len(self._costs) if self._costs else 0

    @property
    def success_rate(self) -> float:
        return self._successes / self._total if self._total > 0 else 0

    @property
    def sample_count(self) -> int:
        return self._total


class DecisionGraphService(BaseService):
    def __init__(self, settings: DecisionGraphSettings) -> None:
        super().__init__()
        self._settings = settings
        self._graphs: dict[str, DecisionGraph] = {}
        self._performance: dict[str, dict[str, PathPerformance]] = defaultdict(dict)

    def register_graph(self, graph: DecisionGraph) -> None:
        self._graphs[str(graph.id)] = graph
        for path in graph.paths:
            self._performance[str(graph.id)].setdefault(path.id, PathPerformance())
        logger.info(f"Decision graph registered: {graph.name}")

    def select_path(self, graph_id: str, runtime_vars: dict) -> ExecutionPath | None:
        graph = self._graphs.get(graph_id)
        if graph is None:
            return None

        for path in graph.paths:
            if self._matches_conditions(path, runtime_vars):
                return path

        if graph.fallback_paths:
            return graph.fallback_paths[0]

        return graph.paths[0] if graph.paths else None

    def get_fallback_path(self, graph_id: str, failed_path_id: str, depth: int = 0) -> ExecutionPath | None:
        if depth >= self._settings.max_fallback_depth:
            return None

        graph = self._graphs.get(graph_id)
        if graph is None:
            return None

        for i, path in enumerate(graph.paths):
            if path.id == failed_path_id:
                if graph.fallback_paths:
                    return graph.fallback_paths[min(depth, len(graph.fallback_paths) - 1)]
                if i + 1 < len(graph.paths):
                    return graph.paths[i + 1]

        return None

    def record_path_result(self, graph_id: str, path_id: str, latency_ms: float, cost: float, success: bool) -> None:
        perf = self._performance.get(graph_id, {}).get(path_id)
        if perf is None:
            perf = PathPerformance()
            self._performance.setdefault(graph_id, {})[path_id] = perf
        perf.record(latency_ms, cost, success)

    def get_path_stats(self, graph_id: str) -> dict[str, dict]:
        stats = {}
        for path_id, perf in self._performance.get(graph_id, {}).items():
            stats[path_id] = {
                "avg_latency_ms": perf.avg_latency_ms,
                "avg_cost": perf.avg_cost,
                "success_rate": perf.success_rate,
                "sample_count": perf.sample_count,
            }
        return stats

    def _matches_conditions(self, path: ExecutionPath, runtime_vars: dict) -> bool:
        if not path.conditions:
            return True

        expr = path.conditions.get("_expr")
        if expr and isinstance(expr, str):
            return evaluate_expression(expr, runtime_vars)

        # Fallback: simple key-value matching for non-expression conditions
        for key, expected in path.conditions.items():
            if key == "_expr":
                continue
            actual = runtime_vars.get(key)
            if actual != expected:
                return False
        return True
