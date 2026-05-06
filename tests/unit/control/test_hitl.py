"""Unit tests for HITL service."""

import pytest
from uuid import uuid4

from omniagent.common.events import EventBus
from omniagent.control.models.approval import ApprovalDecision, ApprovalStatus
from omniagent.control.services.hitl import HITLService
from omniagent.settings import HITLSettings


@pytest.fixture
def hitl():
    return HITLService(settings=HITLSettings(), event_bus=EventBus())


@pytest.mark.unit
async def test_create_approval_request(hitl):
    request = await hitl.create_approval_request(
        execution_id=uuid4(),
        node_id="approve-node",
        context_summary={"action": "deploy"},
    )
    assert request.status == ApprovalStatus.PENDING
    assert request.node_id == "approve-node"
    assert len(hitl.list_pending()) == 1


@pytest.mark.unit
async def test_approve(hitl):
    request = await hitl.create_approval_request(uuid4(), "node", {})
    result = await hitl.decide(
        str(request.id),
        ApprovalDecision(decision="approve", reason="looks good", approver_id="admin"),
    )
    assert result.status == ApprovalStatus.APPROVED
    assert result.approver_id == "admin"
    assert len(hitl.list_pending()) == 0


@pytest.mark.unit
async def test_reject(hitl):
    request = await hitl.create_approval_request(uuid4(), "node", {})
    result = await hitl.decide(
        str(request.id),
        ApprovalDecision(decision="reject", reason="too risky"),
    )
    assert result.status == ApprovalStatus.REJECTED
