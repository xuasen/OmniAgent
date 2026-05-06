"""Unit tests for proxy hooks."""

import pytest

from omniagent.common.events import EventBus
from omniagent.proxy.hooks.base import HookContext
from omniagent.proxy.hooks.policy_hook import PolicyHook
from omniagent.proxy.hooks.trace_hook import TraceHook
from omniagent.proxy.hooks.experiment_hook import ExperimentHook


def make_context(**kwargs) -> HookContext:
    defaults = {
        "request_body": {"model": "gpt-4", "messages": []},
        "headers": {},
        "path": "/v1/chat/completions",
    }
    defaults.update(kwargs)
    return HookContext(**defaults)


@pytest.mark.unit
async def test_policy_hook_passes_without_engine():
    hook = PolicyHook(policy_engine=None)
    ctx = make_context()
    result = await hook.pre_forward(ctx)
    assert result.rejected is False


@pytest.mark.unit
async def test_trace_hook_publishes_event():
    bus = EventBus()
    events_received = []
    async def _capture(e):
        events_received.append(e)
    bus.subscribe("trace.step", _capture)

    hook = TraceHook(event_bus=bus)
    ctx = make_context(agent_id="test-agent", trace_id="trace-123")

    response_body = {
        "model": "gpt-4",
        "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        "usage": {"total_tokens": 50},
    }
    await hook.post_forward(ctx, response_body, 200)

    # Give async tasks time to complete
    import asyncio
    await asyncio.sleep(0.01)

    assert len(events_received) == 1
    assert events_received[0].payload["agent_id"] == "test-agent"
    assert events_received[0].payload["tokens_used"] == 50
    assert events_received[0].payload["step_type"] == "thought"


@pytest.mark.unit
async def test_trace_hook_skips_on_error_status():
    bus = EventBus()
    events_received = []
    async def _capture(e):
        events_received.append(e)
    bus.subscribe("trace.step", _capture)

    hook = TraceHook(event_bus=bus)
    ctx = make_context()
    await hook.post_forward(ctx, {"error": "bad request"}, 400)

    import asyncio
    await asyncio.sleep(0.01)

    assert len(events_received) == 0


@pytest.mark.unit
async def test_trace_hook_detects_tool_calls():
    bus = EventBus()
    events_received = []
    async def _capture(e):
        events_received.append(e)
    bus.subscribe("trace.step", _capture)

    hook = TraceHook(event_bus=bus)
    ctx = make_context()
    response_body = {
        "model": "gpt-4",
        "choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            {"function": {"name": "search", "arguments": "{}"}}
        ]}}],
        "usage": {"total_tokens": 30},
    }
    await hook.post_forward(ctx, response_body, 200)

    import asyncio
    await asyncio.sleep(0.01)

    assert len(events_received) == 1
    assert events_received[0].payload["step_type"] == "action"
    assert "search" in events_received[0].payload["tool_calls"]
