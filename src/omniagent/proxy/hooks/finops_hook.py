"""Pre-forward hook: model routing and cost tier selection."""

import logging

from omniagent.intelligence.services.finops import FinOpsService
from omniagent.proxy.hooks.base import HookContext

logger = logging.getLogger(__name__)


class FinOpsHook:
    def __init__(self, finops: FinOpsService) -> None:
        self._finops = finops

    async def pre_forward(self, context: HookContext) -> HookContext:
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
