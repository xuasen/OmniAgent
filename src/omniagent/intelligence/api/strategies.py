"""Strategy API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.intelligence.models.strategy import StrategyDefinition

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
async def list_strategies() -> list[dict]:
    return []


@router.post("", status_code=201)
async def create_strategy(strategy: StrategyDefinition) -> dict:
    return {"id": str(strategy.id), "name": strategy.name, "status": "created"}


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: UUID) -> dict:
    raise NotImplementedError


@router.put("/{strategy_id}")
async def update_strategy(strategy_id: UUID, strategy: StrategyDefinition) -> dict:
    raise NotImplementedError


@router.post("/{strategy_id}/evaluate")
async def evaluate_strategy(strategy_id: UUID) -> dict:
    raise NotImplementedError


@router.get("/{strategy_id}/decisions")
async def list_decisions(strategy_id: UUID) -> list[dict]:
    return []
