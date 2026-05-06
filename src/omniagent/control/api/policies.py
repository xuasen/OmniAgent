"""Policy API endpoints."""

from uuid import UUID

from fastapi import APIRouter

from omniagent.control.models.policy import PolicyCreate, PolicyRule

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("")
async def list_policies() -> list[dict]:
    return []


@router.post("", status_code=201)
async def create_policy(policy: PolicyCreate) -> dict:
    raise NotImplementedError


@router.get("/{policy_id}")
async def get_policy(policy_id: UUID) -> dict:
    raise NotImplementedError


@router.put("/{policy_id}")
async def update_policy(policy_id: UUID, policy: PolicyCreate) -> dict:
    raise NotImplementedError


@router.delete("/{policy_id}")
async def delete_policy(policy_id: UUID) -> dict:
    raise NotImplementedError


@router.get("/quotas/{identity}")
async def get_quota_usage(identity: str) -> dict:
    raise NotImplementedError
