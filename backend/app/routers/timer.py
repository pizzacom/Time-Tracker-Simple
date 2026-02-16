"""Timer state routes (server-side timer persistence)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.timer_state import TimerState
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/timer", tags=["Timer"])


class TimerStartRequest(BaseModel):
    start_time: datetime
    description: str | None = None


class TimerResponse(BaseModel):
    is_running: bool
    start_time: datetime | None = None
    description: str | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=TimerResponse)
async def get_timer(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current timer state for the logged-in user."""
    result = await db.execute(
        select(TimerState).where(TimerState.user_id == user.id)
    )
    state = result.scalar_one_or_none()
    if not state:
        return TimerResponse(is_running=False)
    return TimerResponse(
        is_running=True,
        start_time=state.start_time,
        description=state.description,
    )


@router.put("", response_model=TimerResponse)
async def start_timer(
    body: TimerStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start or update the timer for the logged-in user."""
    result = await db.execute(
        select(TimerState).where(TimerState.user_id == user.id)
    )
    state = result.scalar_one_or_none()
    if state:
        state.start_time = body.start_time
        state.description = body.description
    else:
        state = TimerState(
            user_id=user.id,
            start_time=body.start_time,
            description=body.description,
        )
        db.add(state)
    return TimerResponse(
        is_running=True,
        start_time=state.start_time,
        description=state.description,
    )


@router.delete("")
async def stop_timer(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear the timer state (called when timer is stopped or reset)."""
    await db.execute(
        delete(TimerState).where(TimerState.user_id == user.id)
    )
    return {"message": "Timer cleared"}
