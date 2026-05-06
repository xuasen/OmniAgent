"""FinOps API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.intelligence.models.finops import ModelRoute

router = APIRouter(prefix="/finops", tags=["finops"])


@router.get("/routes")
async def list_routes() -> list[dict]:
    return []


@router.post("/routes", status_code=201)
async def create_route(route: ModelRoute) -> dict:
    return {"id": str(route.id), "model_id": route.model_id, "status": "created"}


@router.put("/routes/{route_id}")
async def update_route(route_id: UUID, route: ModelRoute) -> dict:
    raise NotImplementedError


@router.get("/costs")
async def get_costs() -> dict:
    return {"total_cost_usd": 0.0, "by_model": {}, "by_workflow": {}}


@router.get("/costs/summary")
async def get_cost_summary() -> dict:
    return {"total_cost_usd": 0.0, "downgrade_count": 0}
