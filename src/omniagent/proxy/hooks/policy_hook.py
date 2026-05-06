"""Pre-forward hook: policy enforcement (ACL, quotas)."""

import logging

from omniagent.proxy.hooks.base import HookContext

logger = logging.getLogger(__name__)


class PolicyHook:
    def __init__(self, policy_engine: "PolicyEngineService | None" = None) -> None:
        self._policy_engine = policy_engine

    async def pre_forward(self, context: HookContext) -> HookContext:
        if self._policy_engine is None:
            return context

        try:
            await self._policy_engine.evaluate(
                identity=context.identity,
                action=f"llm_call:{context.request_body.get('model', 'unknown')}",
                context={"path": context.path, "agent_id": context.agent_id},
            )
        except Exception as e:
            context.rejected = True
            context.reject_status = 403
            context.reject_body = {
                "error": {"message": str(e), "type": "policy_violation", "code": "quota_exceeded"}
            }
            logger.info(f"Request blocked by policy: {e}")

        return context
