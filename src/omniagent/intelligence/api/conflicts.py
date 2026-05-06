"""Conflict resolution API endpoints."""

from uuid import UUID

from fastapi import APIRouter

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("")
async def list_conflicts() -> list[dict]:
    return []


@router.get("/{conflict_id}")
async def get_conflict(conflict_id: UUID) -> dict:
    raise NotImplementedError
