"""ORM models for persisted state.

`InferenceLog` mirrors the PRD Section 5.2 schema exactly. The `input_payload`
column uses `JSONB` on PostgreSQL (the production target) and falls back to
`JSON` on SQLite (used by the test suite). The migration in
`alembic/versions/0001_create_inference_logs.py` is the authoritative DDL;
this model is the runtime view the API uses to insert rows.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InferenceLog(Base):
    __tablename__ = "inference_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_payload: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    is_drift_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


Index("idx_timestamp", InferenceLog.timestamp)
