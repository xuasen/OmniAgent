"""Sandboxed tool execution for replay isolation (Req 13)."""

import logging

from omniagent.common.base_service import BaseService

logger = logging.getLogger(__name__)


class SandboxExecutor(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self._allowed_tools: set[str] = set()

    def configure(self, allowed_tools: list[str]) -> None:
        self._allowed_tools = set(allowed_tools)

    async def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name not in self._allowed_tools:
            logger.warning(f"Tool '{tool_name}' not sandboxable, skipping")
            return {"status": "skipped", "reason": "not_sandboxable", "tool": tool_name}

        # Stub: actual sandboxed execution
        logger.info(f"Sandbox executing tool: {tool_name}")
        return {"status": "completed", "tool": tool_name, "output": {}}

    def is_sandboxable(self, tool_name: str) -> bool:
        return tool_name in self._allowed_tools
