"""Policy domain models."""

from enum import Enum

from pydantic import Field

from omniagent.common.base_model import EntityModel, OmniBaseModel


class PolicyType(str, Enum):
    ACL = "acl"
    TOKEN_QUOTA = "token_quota"
    TOOL_ACCESS = "tool_access"


class PolicyRule(EntityModel):
    name: str
    policy_type: PolicyType
    identity: str | None = None
    workflow_id: str | None = None
    rule: dict = Field(default_factory=dict)
    enabled: bool = True


class PolicyViolation(OmniBaseModel):
    policy_id: str
    violation_type: str
    current_usage: float | None = None
    limit: float | None = None
    message: str


class PolicyCreate(OmniBaseModel):
    name: str
    policy_type: PolicyType
    identity: str | None = None
    workflow_id: str | None = None
    rule: dict = Field(default_factory=dict)
    enabled: bool = True
