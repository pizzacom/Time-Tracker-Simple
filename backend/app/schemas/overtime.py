"""Overtime schemas."""
import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class OvertimeUseRequest(BaseModel):
    date: date
    minutes: int = Field(..., gt=0)
    note: Optional[str] = None


class OvertimeLedgerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    date: date
    minutes: int
    reason: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OvertimeBalanceResponse(BaseModel):
    user_id: uuid.UUID
    balance_minutes: int
    history: List[OvertimeLedgerResponse] = []
