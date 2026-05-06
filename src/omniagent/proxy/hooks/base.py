"""Hook protocols for proxy request interception."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class HookContext:
    request_body: dict
    headers: dict[str, str]
    path: str
    identity: str = ""
    agent_id: str = ""
    trace_id: str = ""
    selected_model: str | None = None
    selected_endpoint: str | None = None
    rejected: bool = False
    reject_status: int = 403
    reject_body: dict = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PreForwardHook(Protocol):
    async def pre_forward(self, context: HookContext) -> HookContext: ...


@runtime_checkable
class PostForwardHook(Protocol):
    async def post_forward(self, context: HookContext, response_body: dict, status_code: int) -> None: ...
