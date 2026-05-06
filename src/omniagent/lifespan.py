"""Application startup and shutdown lifecycle."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from omniagent.db.engine import init_engine, close_engine
from omniagent.logging import setup_logging
from omniagent.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.server.log_level)
    logger.info("OmniAgent starting up...")

    init_engine(
        url=settings.database.url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.pool_max_overflow,
    )
    logger.info("Database engine initialized")

    # Initialize proxy
    from omniagent.proxy.upstream import UpstreamPool
    from omniagent.proxy.handler import ProxyHandler
    from omniagent.proxy.hooks.trace_hook import TraceHook
    from omniagent.proxy.hooks.policy_hook import PolicyHook
    from omniagent.common.events import EventBus

    upstream_url = getattr(settings, "proxy", None)
    base_url = upstream_url.upstream_url if upstream_url else "https://api.openai.com"

    upstream = UpstreamPool(default_base_url=base_url)
    await upstream.start()

    event_bus = EventBus()
    pre_hooks = [PolicyHook()]
    post_hooks = [TraceHook(event_bus)]

    app.state.proxy_handler = ProxyHandler(
        upstream=upstream, pre_hooks=pre_hooks, post_hooks=post_hooks
    )
    app.state.upstream_pool = upstream
    logger.info(f"Proxy initialized: upstream={base_url}")

    yield

    logger.info("OmniAgent shutting down...")
    await upstream.stop()
    await close_engine()
    logger.info("Shutdown complete")
