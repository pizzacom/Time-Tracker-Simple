"""Department schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    leader_id: Optional[uuid.UUID] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    leader_id: Optional[uuid.UUID] = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    leader_id: Optional[uuid.UUID] = None
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True
