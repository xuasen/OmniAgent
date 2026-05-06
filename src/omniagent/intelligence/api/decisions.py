"""Decision graph API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.intelligence.models.decision_graph import DecisionGraph

router = APIRouter(prefix="/decisions/graphs", tags=["decisions"])


@router.get("")
async def list_graphs() -> list[dict]:
    return []


@router.post("", status_code=201)
async def create_graph(graph: DecisionGraph) -> dict:
    return {"id": str(graph.id), "name": graph.name, "status": "created"}


@router.get("/{graph_id}")
async def get_graph(graph_id: UUID) -> dict:
    raise NotImplementedError


@router.put("/{graph_id}")
async def update_graph(graph_id: UUID, graph: DecisionGraph) -> dict:
    raise NotImplementedError
