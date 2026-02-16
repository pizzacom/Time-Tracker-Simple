"""TimeEntry model."""
import uuid
from datetime import datetime, date as date_type, time as time_type

from sqlalchemy import (
    String, Integer, Text, Date, Time, DateTime,
    ForeignKey, Enum as SAEnum, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_type: Mapped[str] = mapped_column(
        SAEnum("regular", "overtime_used", name="entry_type"),
        default="regular",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("work_minutes >= 0", name="work_time_positive"),
    )

    # Relationships
    user = relationship("User", back_populates="time_entries")
