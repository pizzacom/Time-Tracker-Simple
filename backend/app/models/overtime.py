"""Overtime ledger model (immutable, append-only)."""
import uuid
from datetime import datetime, date as date_type

from sqlalchemy import Integer, Text, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class OvertimeLedger(Base):
    __tablename__ = "overtime_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(
        SAEnum("earned", "used", "adjustment", name="overtime_reason"),
        nullable=False,
    )
    related_time_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("time_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="overtime_entries")
    related_entry = relationship("TimeEntry")
