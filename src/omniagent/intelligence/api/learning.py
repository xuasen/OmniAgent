"""Learning loop API endpoints."""

from uuid import UUID

from fastapi import APIRouter

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/adjustments")
async def list_adjustments() -> list[dict]:
    return []


@router.get("/adjustments/{adjustment_id}")
async def get_adjustment(adjustment_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/adjustments/{adjustment_id}/approve")
async def approve_adjustment(adjustment_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/adjustments/{adjustment_id}/reject")
async def reject_adjustment(adjustment_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/trigger")
async def trigger_learning() -> dict:
    raise NotImplementedError
