"""User model."""
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("admin", "abteilungsleiter", "worker", name="user_role"),
        nullable=False,
        default="worker",
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    # Relationships
    department = relationship("Department", back_populates="members", foreign_keys=[department_id])
    time_entries = relationship("TimeEntry", back_populates="user", cascade="all, delete-orphan")
    work_schedules = relationship("WorkSchedule", back_populates="user", cascade="all, delete-orphan")
    overtime_entries = relationship("OvertimeLedger", back_populates="user", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="user", cascade="all, delete-orphan")
    vacation_budgets = relationship("VacationBudget", back_populates="user", cascade="all, delete-orphan")
    timer_state = relationship("TimerState", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
