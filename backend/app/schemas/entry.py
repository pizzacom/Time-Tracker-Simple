"""Time entry schemas."""
import uuid
from datetime import date as date_type, time as time_type, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class EntryBase(BaseModel):
    date: date_type
    start_time: time_type
    end_time: time_type
    break_minutes: int = Field(default=0, ge=0)
    description: Optional[str] = None


class EntryCreate(EntryBase):
    pass


class EntryUpdate(BaseModel):
    date: Optional[date_type] = None
    start_time: Optional[time_type] = None
    end_time: Optional[time_type] = None
    break_minutes: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def coerce_empty_strings(cls, values):
        """Convert empty strings to None for optional fields."""
        if isinstance(values, dict):
            for key in ("date", "start_time", "end_time", "description"):
                if key in values and values[key] == "":
                    values[key] = None
        return values


class EntryResponse(EntryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    work_minutes: int
    entry_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntryWithUser(EntryResponse):
    user_name: Optional[str] = None
