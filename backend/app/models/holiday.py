"""Holiday model (company-wide public holidays / Feiertage)."""
import uuid
from datetime import datetime, date as date_type

from sqlalchemy import String, Boolean, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, utc_now


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date_type] = mapped_column(Date, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
