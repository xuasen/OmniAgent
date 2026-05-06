"""Experiment API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.intelligence.models.experiment import ExperimentCreate

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
async def list_experiments() -> list[dict]:
    return []


@router.post("", status_code=201)
async def create_experiment(experiment: ExperimentCreate) -> dict:
    return {"id": str(UUID(int=0)), "name": experiment.name, "status": "draft"}


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/{experiment_id}/stop")
async def stop_experiment(experiment_id: UUID) -> dict:
    raise NotImplementedError


@router.get("/{experiment_id}/report")
async def get_report(experiment_id: UUID) -> dict:
    raise NotImplementedError
