"""Human-in-the-loop approval service (Req 6)."""

import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.common.events import Event, EventBus
from omniagent.control.models.approval import ApprovalDecision, ApprovalRequest, ApprovalStatus
from omniagent.settings import HITLSettings

logger = logging.getLogger(__name__)


class HITLService(BaseService):
    def __init__(self, settings: HITLSettings, event_bus: EventBus) -> None:
        super().__init__()
        self._settings = settings
        self._event_bus = event_bus
        self._pending: dict[str, ApprovalRequest] = {}

    async def create_approval_request(
        self, execution_id: UUID, node_id: str, context_summary: dict
    ) -> ApprovalRequest:
        timeout_at = datetime.utcnow() + timedelta(minutes=self._settings.default_timeout_minutes)
        request = ApprovalRequest(
            id=uuid4(),
            execution_id=execution_id,
            node_id=node_id,
            context_summary=context_summary,
            timeout_at=timeout_at,
        )
        self._pending[str(request.id)] = request

        await self._event_bus.publish(Event(
            event_type="hitl.approval_requested",
            payload={
                "approval_id": str(request.id),
                "execution_id": str(execution_id),
                "node_id": node_id,
            },
            source="hitl",
        ))
        return request

    async def decide(self, approval_id: str, decision: ApprovalDecision) -> ApprovalRequest:
        request = self._pending.get(approval_id)
        if request is None:
            raise ValueError(f"Approval request not found: {approval_id}")

        request.status = ApprovalStatus.APPROVED if decision.decision == "approve" else ApprovalStatus.REJECTED
        request.approver_id = decision.approver_id
        request.decision_reason = decision.reason
        request.decided_at = datetime.utcnow()

        del self._pending[approval_id]

        await self._event_bus.publish(Event(
            event_type="hitl.decision_made",
            payload={
                "approval_id": approval_id,
                "decision": decision.decision,
                "approver_id": decision.approver_id,
            },
            source="hitl",
        ))
        return request

    async def check_timeouts(self) -> list[ApprovalRequest]:
        now = datetime.utcnow()
        timed_out: list[ApprovalRequest] = []
        for approval_id, request in list(self._pending.items()):
            if request.timeout_at and now >= request.timeout_at:
                if self._settings.default_timeout_action == "reject":
                    request.status = ApprovalStatus.TIMEOUT
                else:
                    request.escalation_level += 1
                del self._pending[approval_id]
                timed_out.append(request)
        return timed_out

    def list_pending(self) -> list[ApprovalRequest]:
        return list(self._pending.values())
