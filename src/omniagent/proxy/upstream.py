"""HTTP client pool for upstream LLM providers."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class UpstreamPool:
    def __init__(self, default_base_url: str, timeout: float = 60.0) -> None:
        self._default_base_url = default_base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        logger.info(f"Upstream pool started: {self._default_base_url}")

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def forward(
        self,
        path: str,
        body: bytes,
        headers: dict[str, str],
        base_url: str | None = None,
    ) -> httpx.Response:
        url = (base_url or self._default_base_url) + path
        client = self._get_client()
        forward_headers = {
            k: v for k, v in headers.items()
            if k.lower() in ("authorization", "content-type", "accept")
        }
        forward_headers.setdefault("content-type", "application/json")
        return await client.post(url, content=body, headers=forward_headers)

    async def forward_stream(
        self,
        path: str,
        body: bytes,
        headers: dict[str, str],
        base_url: str | None = None,
    ):
        url = (base_url or self._default_base_url) + path
        client = self._get_client()
        forward_headers = {
            k: v for k, v in headers.items()
            if k.lower() in ("authorization", "content-type", "accept")
        }
        forward_headers.setdefault("content-type", "application/json")
        async with client.stream("POST", url, content=body, headers=forward_headers) as response:
            async for chunk in response.aiter_bytes():
                yield chunk

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Upstream pool not started")
        return self._client
