"""API v1 router — mounts control and intelligence routers + trace CRUD."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from omniagent.control.api.router import router as control_router
from omniagent.intelligence.api.router import router as intelligence_router

router = APIRouter()

router.include_router(control_router)
router.include_router(intelligence_router)


# Trace endpoints (migrated from execution layer)
from omniagent.common.trace import Trace, TraceQuery, TraceStatus

traces_router = APIRouter(prefix="/traces", tags=["traces"])


@traces_router.get("")
async def list_traces(
    agent_id: str | None = None,
    adapter_id: str | None = None,
    status: TraceStatus | None = None,
    min_cost: float | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict]:
    return []


@traces_router.get("/{trace_id}")
async def get_trace(trace_id: UUID) -> dict:
    raise NotImplementedError


router.include_router(traces_router)
