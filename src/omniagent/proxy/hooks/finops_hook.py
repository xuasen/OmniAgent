"""Pre-forward hook: model routing, cost tier selection, and budget enforcement."""

import logging

from omniagent.intelligence.models.finops import BudgetAction
from omniagent.intelligence.services.finops import FinOpsService
from omniagent.proxy.hooks.base import HookContext

logger = logging.getLogger(__name__)


class FinOpsHook:
    def __init__(self, finops: FinOpsService, default_budget_action: BudgetAction = BudgetAction.DOWNGRADE) -> None:
        self._finops = finops
        self._default_action = default_budget_action

    async def pre_forward(self, context: HookContext) -> HookContext:
        # 1. Route to appropriate model tier
        try:
            route = await self._finops.route_request({
                "user_tier": context.metadata.get("user_tier", "default"),
                "agent_id": context.agent_id,
                "requested_model": context.request_body.get("model", ""),
            })
            context.selected_model = route.model_id
            context.selected_endpoint = route.endpoint
            context.metadata["cost_tier"] = route.cost_tier
            context.metadata["cost_per_1k"] = route.cost_per_1k_tokens
        except Exception as e:
            logger.warning(f"FinOps routing failed, using original model: {e}")
            return context

        # 2. Check real-time budget (based on actual recorded costs)
        execution_id = context.metadata.get("execution_id", context.agent_id)
        cost_limit = context.metadata.get("cost_limit")
        if execution_id and cost_limit:
            result = await self._finops.check_budget(execution_id, cost_limit, self._default_action)
            if result["over_budget"]:
                if result["action"] == "reject":
                    context.rejected = True
                    context.reject_status = 429
                    context.reject_body = {
                        "error": {
                            "message": f"Budget exceeded: ${result['current_cost']:.4f} >= ${result['limit']:.4f}",
                            "type": "budget_exceeded",
                            "code": "over_budget",
                        }
                    }
                elif result["action"] == "downgrade" and result.get("downgraded_to"):
                    context.selected_model = result["downgraded_to"]
                    logger.info(f"Budget exceeded, downgraded to: {result['downgraded_to']}")

        return context
