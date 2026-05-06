"""Unit tests for proxy handler."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from omniagent.app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_proxy_chat_completions_returns_503_before_init(client):
    """Proxy should return 503 if upstream not initialized (lifespan didn't run)."""
    response = await client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4", "messages": [{"role": "user", "content": "hello"}]},
    )
    # Without lifespan, proxy_handler is not set → 503
    assert response.status_code == 503
    assert "Proxy not initialized" in response.json()["error"]["message"]


@pytest.mark.unit
async def test_proxy_embeddings_returns_503(client):
    response = await client.post(
        "/v1/embeddings",
        json={"model": "text-embedding-3-small", "input": "test"},
    )
    assert response.status_code == 503
