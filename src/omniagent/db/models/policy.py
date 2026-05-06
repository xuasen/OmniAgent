"""Policy ORM models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Boolean, BigInteger, Numeric, DateTime, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from omniagent.db.base import Base


class PolicyModel(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule: Mapped[dict] = mapped_column(JSONB, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_policies_type", "policy_type"),
        Index("idx_policies_identity", "identity"),
    )


class QuotaUsageModel(Base):
    __tablename__ = "quota_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    identity: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tokens_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cost_used_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("policy_id", "identity", "period_start", name="uq_quota_usage_unique"),
    )
