"""Workflow API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from omniagent.control.models.workflow import WorkflowCreate, WorkflowDefinition
from omniagent.dependencies import get_orchestrator
from omniagent.control.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("")
async def list_workflows() -> list[dict]:
    return []


@router.post("", status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> dict:
    wf = WorkflowDefinition(**workflow.model_dump())
    orchestrator.validate_workflow(wf)
    return {"id": str(wf.id), "name": wf.name, "version": wf.version, "status": "created"}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: UUID) -> dict:
    raise NotImplementedError


@router.post("/{workflow_id}/validate")
async def validate_workflow(workflow: WorkflowCreate) -> dict:
    return {"valid": True}
