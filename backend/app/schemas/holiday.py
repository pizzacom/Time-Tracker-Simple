"""Holiday schemas."""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class HolidayCreate(BaseModel):
    date: date
    name: str = Field(..., max_length=255)
    is_half_day: bool = False
    region: Optional[str] = Field(None, max_length=50)


class HolidayResponse(BaseModel):
    id: uuid.UUID
    date: date
    name: str
    is_half_day: bool
    region: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
