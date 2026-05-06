"""HITL approval API endpoints."""

from fastapi import APIRouter

from omniagent.control.models.approval import ApprovalDecision, ApprovalRequest

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
async def list_pending_approvals() -> list[dict]:
    return []


@router.get("/{approval_id}")
async def get_approval(approval_id: str) -> dict:
    raise NotImplementedError


@router.post("/{approval_id}/decide")
async def decide_approval(approval_id: str, decision: ApprovalDecision) -> dict:
    raise NotImplementedError
