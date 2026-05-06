"""Policy engine — governance, ACL, quotas, tool access (Req 8)."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniagent.common.base_service import BaseService
from omniagent.control.models.policy import PolicyRule, PolicyType, PolicyViolation
from omniagent.db.models.policy import PolicyModel, QuotaUsageModel
from omniagent.exceptions import PolicyViolationError
from omniagent.settings import PolicyEngineSettings

logger = logging.getLogger(__name__)


class PolicyEngineService(BaseService):
    def __init__(self, session: AsyncSession, settings: PolicyEngineSettings) -> None:
        super().__init__()
        self._session = session
        self._settings = settings

    async def evaluate(self, identity: str, action: str, context: dict) -> None:
        policies = await self._load_policies(identity)

        for policy in policies:
            if not policy.enabled:
                continue

            if policy.policy_type == PolicyType.ACL:
                self._check_acl(policy, identity, action)
            elif policy.policy_type == PolicyType.TOKEN_QUOTA:
                await self._check_quota(policy, identity)
            elif policy.policy_type == PolicyType.TOOL_ACCESS:
                self._check_tool_access(policy, action, context)

    def _check_acl(self, policy: PolicyRule, identity: str, action: str) -> None:
        allowed_actions = policy.rule.get("allowed_actions", [])
        if allowed_actions and action not in allowed_actions:
            raise PolicyViolationError(
                f"Action '{action}' not allowed for identity '{identity}'",
                details={
                    "policy_id": str(policy.id),
                    "violation_type": "acl",
                    "action": action,
                },
            )

    async def _check_quota(self, policy: PolicyRule, identity: str) -> None:
        quota_limit = policy.rule.get("max_tokens")
        if quota_limit is None:
            return

        stmt = select(QuotaUsageModel).where(
            QuotaUsageModel.policy_id == policy.id,
            QuotaUsageModel.identity == identity,
        )
        result = await self._session.execute(stmt)
        usage = result.scalar_one_or_none()

        if usage and usage.tokens_used >= quota_limit:
            raise PolicyViolationError(
                f"Token quota exceeded for identity '{identity}'",
                details={
                    "policy_id": str(policy.id),
                    "violation_type": "quota_exceeded",
                    "current_usage": usage.tokens_used,
                    "limit": quota_limit,
                },
            )

    def _check_tool_access(self, policy: PolicyRule, action: str, context: dict) -> None:
        blocked_tools = policy.rule.get("blocked_tools", [])
        tool_name = context.get("tool_name", "")
        if tool_name in blocked_tools:
            raise PolicyViolationError(
                f"Tool '{tool_name}' is blocked by policy",
                details={
                    "policy_id": str(policy.id),
                    "violation_type": "tool_access",
                    "tool_name": tool_name,
                },
            )

    async def _load_policies(self, identity: str) -> list[PolicyRule]:
        stmt = select(PolicyModel).where(
            (PolicyModel.identity == identity) | (PolicyModel.identity.is_(None))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            PolicyRule(
                id=m.id,
                name=m.name,
                policy_type=PolicyType(m.policy_type),
                identity=m.identity,
                workflow_id=m.workflow_id,
                rule=m.rule,
                enabled=m.enabled,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def create_policy(self, policy: PolicyRule) -> PolicyRule:
        model = PolicyModel(
            id=policy.id,
            name=policy.name,
            policy_type=policy.policy_type.value if isinstance(policy.policy_type, PolicyType) else policy.policy_type,
            identity=policy.identity,
            workflow_id=policy.workflow_id,
            rule=policy.rule,
            enabled=policy.enabled,
        )
        self._session.add(model)
        await self._session.flush()
        return policy
