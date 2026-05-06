"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from omniagent.app import create_app
from omniagent.common.events import EventBus


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
