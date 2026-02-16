"""Department model."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    leader = relationship("User", foreign_keys=[leader_id])
    members = relationship("User", back_populates="department", foreign_keys="User.department_id")
