"""Timer state model (persists running timer across devices)."""
import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class TimerState(Base):
    __tablename__ = "timer_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="timer_state")
