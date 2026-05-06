"""FastAPI application factory."""

from fastapi import FastAPI, Request

from omniagent.lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title="OmniAgent",
        version="3.0.0",
        description="Enterprise Agent Control Plane + Decision Intelligence Engine",
        lifespan=lifespan,
    )

    from omniagent.api.middleware import register_middleware

    register_middleware(app)

    from omniagent.api.health import router as health_router

    app.include_router(health_router)

    from omniagent.api.v1 import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    # Mount proxy routes for OpenAI-compatible endpoints
    _mount_proxy(app)

    return app


def _mount_proxy(app: FastAPI) -> None:
    """Mount the reverse proxy on OpenAI-compatible paths."""
    from omniagent.proxy.handler import ProxyHandler
    from omniagent.proxy.upstream import UpstreamPool
    from omniagent.proxy.hooks.trace_hook import TraceHook
    from omniagent.common.events import EventBus

    # Lazy initialization — actual startup in lifespan
    @app.post("/v1/chat/completions")
    @app.post("/v1/completions")
    @app.post("/v1/embeddings")
    async def proxy_forward(request: Request):
        handler: ProxyHandler | None = getattr(app.state, "proxy_handler", None)
        if handler is None:
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=503, content={"error": {"message": "Proxy not initialized"}})
        path = request.url.path
        return await handler.handle(request, path)
