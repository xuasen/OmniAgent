"""FastAPI dependency injection container."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from omniagent.common.events import EventBus
from omniagent.db.engine import get_session
from omniagent.settings import Settings, get_settings

_event_bus: EventBus | None = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


def get_app_settings() -> Settings:
    return get_settings()


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def get_trace_store(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> "TraceStoreService":
    from omniagent.db.trace_store import TraceStoreService

    return TraceStoreService(session=session, settings=settings.execution.trace_store)


def get_policy_engine(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> "PolicyEngineService":
    from omniagent.control.services.policy_engine import PolicyEngineService

    return PolicyEngineService(session=session, settings=settings.control.policy_engine)


def get_orchestrator(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
    event_bus: EventBus = Depends(get_event_bus),
) -> "OrchestratorService":
    from omniagent.control.services.orchestrator import OrchestratorService

    return OrchestratorService(session=session, settings=settings.control.orchestrator, event_bus=event_bus)
