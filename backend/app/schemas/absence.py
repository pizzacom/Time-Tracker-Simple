"""Absence schemas."""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class AbsenceCreate(BaseModel):
    date: date
    type: str = Field(..., pattern="^(urlaub|krank|sonderurlaub)$")
    note: Optional[str] = None


class AbsenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    type: str
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VacationBudgetResponse(BaseModel):
    user_id: uuid.UUID
    year: int
    total_days: int
    used_days: int
    remaining_days: int

    class Config:
        from_attributes = True


class VacationBudgetUpdate(BaseModel):
    total_days: int = Field(..., ge=0, le=365)
