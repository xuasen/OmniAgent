"""Replay API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.intelligence.models.replay import BatchReplayRequest, ReplayOverrides

router = APIRouter(prefix="/replays", tags=["replays"])


@router.post("", status_code=201)
async def create_replay(source_trace_id: UUID, overrides: ReplayOverrides) -> dict:
    raise NotImplementedError


@router.post("/batch", status_code=201)
async def create_batch_replay(request: BatchReplayRequest) -> dict:
    raise NotImplementedError


@router.get("/{replay_id}")
async def get_replay(replay_id: UUID) -> dict:
    raise NotImplementedError


@router.get("/{replay_id}/comparison")
async def get_comparison(replay_id: UUID) -> dict:
    raise NotImplementedError
