"""SQLAlchemy ORM models.

Persisted for the history/records/audit views. Deliberately does NOT store raw
biometric embeddings (unless STORE_EMBEDDINGS is explicitly enabled), private
social data, keys, or secrets.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # Face analysis metadata (never the raw vector).
    face_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0)
    face_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    embedding_id: Mapped[str] = mapped_column(String(64), default="")
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=0)
    quality_label: Mapped[str] = mapped_column(String(16), default="")

    # Selected evidence + fingerprint.
    selected_url: Mapped[str] = mapped_column(Text, default="")
    selected_platform: Mapped[str] = mapped_column(String(128), default="")
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    fingerprint: Mapped[str] = mapped_column(String(80), default="")

    # Timing metrics (ms).
    total_ms: Mapped[int] = mapped_column(Integer, default=0)

    events: Mapped[list["PipelineEvent"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )
    record: Mapped["BlockchainRecord | None"] = relationship(
        back_populates="scan", uselist=False, cascade="all, delete-orphan"
    )


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), index=True)
    record_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    fingerprint: Mapped[str] = mapped_column(String(80), index=True)
    transaction_hash: Mapped[str] = mapped_column(String(80), default="")
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    network_chain_id: Mapped[int] = mapped_column(Integer, default=0)
    platform: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    verification_status: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    scan: Mapped["Scan"] = relationship(back_populates="record")


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), index=True)
    event: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    scan: Mapped["Scan"] = relationship(back_populates="events")
