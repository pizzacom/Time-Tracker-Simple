"""Absence model (Urlaub, Krank, Sonderurlaub)."""
import uuid
from datetime import datetime, date as date_type

from sqlalchemy import Text, Date, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[str] = mapped_column(
        SAEnum("urlaub", "krank", "sonderurlaub", name="absence_type"),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date_absence"),
    )

    # Relationships
    user = relationship("User", back_populates="absences")
