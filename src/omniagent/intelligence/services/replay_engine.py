"""Replay engine — replay historical traces with parameter overrides (Req 13)."""

import logging
from uuid import UUID, uuid4

from omniagent.common.base_service import BaseService
from omniagent.exceptions import ReplayError
from omniagent.intelligence.models.replay import (
    BatchReplayReport,
    BatchReplayRequest,
    ComparisonReport,
    ReplayOverrides,
    ReplaySession,
    ReplayStatus,
)
from omniagent.settings import ReplayEngineSettings

logger = logging.getLogger(__name__)


class ReplayEngineService(BaseService):
    def __init__(self, settings: ReplayEngineSettings) -> None:
        super().__init__()
        self._settings = settings
        self._sessions: dict[str, ReplaySession] = {}

    async def create_session(self, source_trace_id: UUID, overrides: ReplayOverrides) -> ReplaySession:
        session = ReplaySession(
            id=uuid4(),
            source_trace_id=source_trace_id,
            overrides=overrides,
            status=ReplayStatus.PENDING,
        )
        self._sessions[str(session.id)] = session
        return session

    async def execute_replay(self, session_id: str) -> ReplaySession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ReplayError(f"Replay session not found: {session_id}")

        session.status = ReplayStatus.RUNNING
        logger.info(f"Executing replay: {session_id}, source_trace={session.source_trace_id}")

        # Stub: actual replay logic would re-execute the trace with overrides in sandbox
        session.status = ReplayStatus.COMPLETED
        session.result_trace_id = uuid4()
        return session

    async def get_comparison(self, session_id: str) -> ComparisonReport:
        session = self._sessions.get(session_id)
        if session is None:
            raise ReplayError(f"Replay session not found: {session_id}")
        if session.status != ReplayStatus.COMPLETED:
            raise ReplayError(f"Replay not completed: {session_id}")

        return ComparisonReport(
            source_trace_id=session.source_trace_id,
            replay_trace_id=session.result_trace_id or uuid4(),
            status_match=True,
            duration_diff_ms=None,
            tokens_diff=None,
            cost_diff_usd=None,
        )

    async def batch_replay(self, request: BatchReplayRequest) -> BatchReplayReport:
        if len(request.source_trace_ids) > self._settings.batch_max_size:
            raise ReplayError(
                f"Batch size {len(request.source_trace_ids)} exceeds max {self._settings.batch_max_size}"
            )

        batch_id = uuid4()
        # Stub: would create and execute sessions in parallel
        return BatchReplayReport(
            batch_id=batch_id,
            total_traces=len(request.source_trace_ids),
            completed=0,
        )

    def get_session(self, session_id: str) -> ReplaySession | None:
        return self._sessions.get(session_id)
