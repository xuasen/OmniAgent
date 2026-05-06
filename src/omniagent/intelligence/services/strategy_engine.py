"""Strategy engine — multi-objective optimization with Pareto + Thompson Sampling (Req 11)."""

import logging
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.exceptions import StrategyError, ValidationError
from omniagent.intelligence.algorithms.pareto import (
    Objective as ParetoObjective,
    compute_pareto_frontier,
    select_from_frontier,
)
from omniagent.intelligence.algorithms.thompson import ThompsonBandit
from omniagent.intelligence.models.strategy import (
    Constraint,
    EvaluationMode,
    Objective,
    StrategyDecision,
    StrategyDefinition,
    ThompsonArmState,
)
from omniagent.settings import StrategyEngineSettings

logger = logging.getLogger(__name__)


class StrategyEngineService(BaseService):
    def __init__(self, settings: StrategyEngineSettings) -> None:
        super().__init__()
        self._settings = settings
        self._strategies: dict[str, StrategyDefinition] = {}
        self._bandits: dict[str, ThompsonBandit] = {}

    def register_strategy(self, strategy: StrategyDefinition) -> None:
        self._validate_definition(strategy)
        self._strategies[str(strategy.id)] = strategy
        logger.info(f"Strategy registered: {strategy.name} v{strategy.version}")

    def register_arm(self, strategy_id: str, arm_id: str, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> None:
        bandit = self._bandits.setdefault(strategy_id, ThompsonBandit())
        bandit.register_arm(arm_id, prior_alpha, prior_beta)

    def update_arm(self, strategy_id: str, arm_id: str, reward: float) -> None:
        bandit = self._bandits.get(strategy_id)
        if bandit:
            bandit.update(arm_id, reward)

    def get_arm_states(self, strategy_id: str) -> list[ThompsonArmState]:
        bandit = self._bandits.get(strategy_id)
        if not bandit:
            return []
        states = []
        for arm_id in bandit.get_expected_values():
            state = bandit.get_state(arm_id)
            if state:
                states.append(ThompsonArmState(
                    arm_id=arm_id, alpha=state.alpha, beta=state.beta,
                    total_pulls=state.total_pulls, expected_value=state.expected_value,
                ))
        return states

    async def evaluate(
        self,
        strategy_id: str,
        candidates: list[dict],
        context: dict | None = None,
        mode: EvaluationMode | None = None,
    ) -> StrategyDecision:
        strategy = self._strategies.get(strategy_id)
        if strategy is None:
            raise StrategyError(f"Strategy not found: {strategy_id}")

        effective_mode = mode or EvaluationMode(strategy.config.get("evaluation_mode", "pareto"))

        feasible = self._filter_feasible(candidates, strategy.constraints)
        if not feasible:
            feasible = candidates

        if effective_mode == EvaluationMode.THOMPSON:
            chosen = self._evaluate_thompson(strategy_id, feasible)
        elif effective_mode == EvaluationMode.PARETO:
            chosen = self._evaluate_pareto(feasible, strategy.objectives)
        else:
            chosen = self._evaluate_weighted(feasible, strategy.objectives)

        pareto_objs = self._to_pareto_objectives(strategy.objectives)
        frontier_size = len(compute_pareto_frontier(feasible, pareto_objs)) if len(feasible) > 1 else len(feasible)

        decision = StrategyDecision(
            id=uuid4(),
            strategy_id=strategy.id,
            chosen_path=chosen or (feasible[0] if feasible else {}),
            candidates=feasible,
            reasoning=self._build_reasoning(effective_mode, chosen, feasible, strategy),
            metrics={"feasible_count": len(feasible), "total_candidates": len(candidates)},
            evaluation_mode=effective_mode,
            pareto_frontier_size=frontier_size,
        )
        return decision

    def _evaluate_pareto(self, candidates: list[dict], objectives: list[Objective]) -> dict | None:
        pareto_objs = self._to_pareto_objectives(objectives)
        frontier = compute_pareto_frontier(candidates, pareto_objs)
        return select_from_frontier(frontier, pareto_objs)

    def _evaluate_thompson(self, strategy_id: str, candidates: list[dict]) -> dict | None:
        bandit = self._bandits.get(strategy_id)
        if not bandit or bandit.arm_count == 0:
            return candidates[0] if candidates else None
        selected_arm = bandit.select_arm()
        for c in candidates:
            if c.get("id") == selected_arm or c.get("name") == selected_arm:
                return c
        return candidates[0] if candidates else None

    def _evaluate_weighted(self, candidates: list[dict], objectives: list[Objective]) -> dict | None:
        if not candidates:
            return None
        best = None
        best_score = float("-inf")
        for c in candidates:
            score = 0.0
            for obj in objectives:
                val = c.get(obj.metric, 0)
                if not isinstance(val, (int, float)):
                    continue
                w = obj.weight * obj.priority
                if obj.direction == "maximize":
                    score += val * w
                else:
                    score -= val * w
            if score > best_score:
                best_score = score
                best = c
        return best

    def _filter_feasible(self, candidates: list[dict], constraints: list[Constraint]) -> list[dict]:
        return [c for c in candidates if self._satisfies_constraints(c, constraints)]

    def _satisfies_constraints(self, candidate: dict, constraints: list[Constraint]) -> bool:
        for constraint in constraints:
            if not constraint.hard:
                continue
            val = candidate.get(constraint.metric)
            if val is None or not isinstance(val, (int, float)):
                continue
            threshold = float(constraint.value) if isinstance(constraint.value, str) else constraint.value
            if not isinstance(threshold, (int, float)):
                continue
            ops = {"<": lambda v, t: v < t, ">": lambda v, t: v > t,
                   "<=": lambda v, t: v <= t, ">=": lambda v, t: v >= t, "==": lambda v, t: v == t}
            op_fn = ops.get(constraint.operator)
            if op_fn and not op_fn(val, threshold):
                return False
        return True

    def _to_pareto_objectives(self, objectives: list[Objective]) -> list[ParetoObjective]:
        return [ParetoObjective(
            metric=o.metric,
            direction=o.direction if isinstance(o.direction, str) else o.direction.value,
            weight=o.weight,
        ) for o in objectives]

    def _build_reasoning(self, mode: EvaluationMode, chosen: dict | None, feasible: list[dict], strategy: StrategyDefinition) -> str:
        name = chosen.get("name", chosen.get("id", "unknown")) if chosen else "none"
        return (
            f"Evaluated {len(feasible)} feasible candidates using {mode.value} mode. "
            f"Selected '{name}' based on {len(strategy.objectives)} objectives "
            f"and {len(strategy.constraints)} constraints."
        )

    def _validate_definition(self, strategy: StrategyDefinition) -> None:
        if not strategy.objectives:
            raise ValidationError("Strategy must have at least one objective")
        for obj in strategy.objectives:
            if obj.metric == "":
                raise ValidationError("Objective metric cannot be empty")
        for constraint in strategy.constraints:
            if constraint.operator not in ("<", ">", "<=", ">=", "=="):
                raise ValidationError(
                    f"Invalid constraint operator: {constraint.operator}",
                    details={"operator": constraint.operator},
                )
