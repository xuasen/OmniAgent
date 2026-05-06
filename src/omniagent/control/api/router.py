"""Control plane router."""

from fastapi import APIRouter

from omniagent.control.api.workflows import router as workflows_router
from omniagent.control.api.approvals import router as approvals_router
from omniagent.control.api.audit import router as audit_router
from omniagent.control.api.policies import router as policies_router

router = APIRouter(tags=["control"])

router.include_router(workflows_router)
router.include_router(approvals_router)
router.include_router(audit_router)
router.include_router(policies_router)
