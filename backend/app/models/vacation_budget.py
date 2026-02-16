"""Vacation budget model (yearly vacation entitlement per worker)."""
import uuid
from datetime import datetime

from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class VacationBudget(Base):
    __tablename__ = "vacation_budgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    used_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("user_id", "year", name="uq_user_year_vacation"),
    )

    # Relationships
    user = relationship("User", back_populates="vacation_budgets")

    @property
    def remaining_days(self) -> int:
        return self.total_days - self.used_days
