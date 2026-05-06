"""Post-forward hook: extract trace events from request/response pairs."""

import logging
from datetime import datetime
from uuid import uuid4

from omniagent.common.events import Event, EventBus
from omniagent.proxy.hooks.base import HookContext

logger = logging.getLogger(__name__)


class TraceHook:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def post_forward(self, context: HookContext, response_body: dict, status_code: int) -> None:
        if status_code >= 400:
            return

        trace_id = context.trace_id or str(uuid4())
        agent_id = context.agent_id or "unknown"
        model = response_body.get("model", context.request_body.get("model", "unknown"))

        # Extract usage
        usage = response_body.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        # Extract messages for Thought content
        choices = response_body.get("choices", [])
        content = ""
        tool_calls = []
        for choice in choices:
            msg = choice.get("message", {})
            if msg.get("content"):
                content = msg["content"]
            if msg.get("tool_calls"):
                tool_calls = msg["tool_calls"]

        # Publish trace step event
        await self._event_bus.publish(Event(
            event_type="trace.step",
            payload={
                "trace_id": trace_id,
                "agent_id": agent_id,
                "model_id": model,
                "step_type": "thought" if content and not tool_calls else "action",
                "content": content[:500] if content else f"tool_calls: {len(tool_calls)}",
                "tokens_used": total_tokens,
                "tool_calls": [tc.get("function", {}).get("name", "") for tc in tool_calls],
                "timestamp": datetime.utcnow().isoformat(),
            },
            source="proxy.trace_hook",
        ))
