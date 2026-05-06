"""Core reverse proxy handler — the main request processing loop."""

from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from omniagent.proxy.hooks.base import HookContext, PostForwardHook, PreForwardHook
from omniagent.proxy.upstream import UpstreamPool

logger = logging.getLogger(__name__)

router = APIRouter()


class ProxyHandler:
    def __init__(
        self,
        upstream: UpstreamPool,
        pre_hooks: list[PreForwardHook] | None = None,
        post_hooks: list[PostForwardHook] | None = None,
    ) -> None:
        self._upstream = upstream
        self._pre_hooks = pre_hooks or []
        self._post_hooks = post_hooks or []

    async def handle(self, request: Request, path: str) -> JSONResponse | StreamingResponse:
        start_time = time.perf_counter()
        body = await request.body()
        try:
            request_body = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return JSONResponse(status_code=400, content={"error": {"message": "Invalid JSON"}})

        headers = {k: v for k, v in request.headers.items()}

        context = HookContext(
            request_body=request_body,
            headers=headers,
            path=path,
            identity=self._extract_identity(headers),
            agent_id=headers.get("x-omniagent-agent-id", ""),
            trace_id=headers.get("x-omniagent-trace-id", ""),
        )

        # Pre-forward hooks
        for hook in self._pre_hooks:
            context = await hook.pre_forward(context)
            if context.rejected:
                return JSONResponse(status_code=context.reject_status, content=context.reject_body)

        # Override model if FinOps selected a different one
        if context.selected_model and "model" in request_body:
            request_body["model"] = context.selected_model
            body = json.dumps(request_body).encode()

        is_stream = request_body.get("stream", False)
        base_url = context.selected_endpoint

        if is_stream:
            return await self._handle_stream(path, body, headers, context, base_url)
        else:
            return await self._handle_json(path, body, headers, context, base_url, start_time)

    async def _handle_json(
        self, path: str, body: bytes, headers: dict, context: HookContext, base_url: str | None, start_time: float
    ) -> JSONResponse:
        response = await self._upstream.forward(path, body, headers, base_url)
        latency_ms = (time.perf_counter() - start_time) * 1000

        try:
            response_body = response.json()
        except Exception:
            response_body = {}

        # Post-forward hooks (async, non-blocking)
        asyncio.create_task(self._run_post_hooks(context, response_body, response.status_code))

        proxy_headers = {
            "x-proxy-latency-ms": f"{latency_ms:.1f}",
            "x-omniagent-model": response_body.get("model", ""),
        }
        return JSONResponse(
            status_code=response.status_code,
            content=response_body,
            headers=proxy_headers,
        )

    async def _handle_stream(
        self, path: str, body: bytes, headers: dict, context: HookContext, base_url: str | None
    ) -> StreamingResponse:
        collected_chunks: list[bytes] = []

        async def generate():
            async for chunk in self._upstream.forward_stream(path, body, headers, base_url):
                collected_chunks.append(chunk)
                yield chunk
            # After stream completes, run post-hooks with collected data
            try:
                full_data = b"".join(collected_chunks)
                # Try to parse accumulated SSE data for post-hooks
                response_body = self._parse_sse_final(full_data)
                asyncio.create_task(self._run_post_hooks(context, response_body, 200))
            except Exception:
                pass

        return StreamingResponse(generate(), media_type="text/event-stream")

    async def _run_post_hooks(self, context: HookContext, response_body: dict, status_code: int) -> None:
        for hook in self._post_hooks:
            try:
                await hook.post_forward(context, response_body, status_code)
            except Exception as e:
                logger.error(f"Post-hook error: {e}")

    def _extract_identity(self, headers: dict[str, str]) -> str:
        auth = headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return token[:16] + "..." if len(token) > 16 else token
        return headers.get("x-omniagent-identity", "anonymous")

    def _parse_sse_final(self, data: bytes) -> dict:
        """Extract the last complete JSON object from SSE stream."""
        text = data.decode(errors="ignore")
        lines = text.strip().split("\n")
        for line in reversed(lines):
            if line.startswith("data: ") and line != "data: [DONE]":
                try:
                    return json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
        return {}
