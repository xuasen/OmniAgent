"""FinOps ORM models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from omniagent.db.base import Base


class ModelRouteModel(Base):
    __tablename__ = "model_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    cost_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    cost_per_1k_tokens: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    max_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    capabilities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CostRecordModel(Base):
    __tablename__ = "cost_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=True
    )
    trace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("traces.id"), nullable=True
    )
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    downgraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_cost_records_execution", "execution_id"),
        Index("idx_cost_records_model", "model_id"),
        Index("idx_cost_records_created_at", "created_at"),
    )
