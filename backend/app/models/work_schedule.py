"""Work schedule model (Soll-Arbeitszeit)."""
import uuid
from datetime import datetime, date as date_type

from sqlalchemy import Integer, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    valid_from: Mapped[date_type] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    monday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    tuesday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    wednesday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    thursday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    friday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    saturday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sunday_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="valid_dates",
        ),
    )

    # Relationships
    user = relationship("User", back_populates="work_schedules")

    def get_minutes_for_weekday(self, weekday: int) -> int:
        """Get target minutes for a given weekday (0=Monday, 6=Sunday)."""
        mapping = {
            0: self.monday_minutes,
            1: self.tuesday_minutes,
            2: self.wednesday_minutes,
            3: self.thursday_minutes,
            4: self.friday_minutes,
            5: self.saturday_minutes,
            6: self.sunday_minutes,
        }
        return mapping.get(weekday, 0)
