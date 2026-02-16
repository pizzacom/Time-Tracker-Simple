"""Work schedule schemas."""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class WorkScheduleBase(BaseModel):
    valid_from: date
    valid_until: Optional[date] = None
    monday_minutes: int = Field(default=480, ge=0, le=1440)
    tuesday_minutes: int = Field(default=480, ge=0, le=1440)
    wednesday_minutes: int = Field(default=480, ge=0, le=1440)
    thursday_minutes: int = Field(default=480, ge=0, le=1440)
    friday_minutes: int = Field(default=480, ge=0, le=1440)
    saturday_minutes: int = Field(default=0, ge=0, le=1440)
    sunday_minutes: int = Field(default=0, ge=0, le=1440)


class WorkScheduleCreate(WorkScheduleBase):
    pass


class WorkScheduleResponse(WorkScheduleBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
