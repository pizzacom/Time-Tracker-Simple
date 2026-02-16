"""Work schedule routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.work_schedule import WorkSchedule
from app.schemas.schedule import WorkScheduleCreate, WorkScheduleResponse
from app.middleware.auth import get_current_user, require_admin_or_leader, check_department_access
from app.services.work_schedule_service import get_current_schedule

router = APIRouter(prefix="/schedule", tags=["Work Schedule"])


@router.get("", response_model=WorkScheduleResponse | None)
async def get_my_schedule(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own current work schedule."""
    schedule = await get_current_schedule(db, user.id)
    if not schedule:
        return None
    return WorkScheduleResponse.model_validate(schedule)


@router.get("/user/{user_id}", response_model=WorkScheduleResponse | None)
async def get_user_schedule(
    user_id: uuid.UUID,
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get a user's current work schedule (admin/boss only)."""
    await check_department_access(user, user_id, db)
    schedule = await get_current_schedule(db, user_id)
    if not schedule:
        return None
    return WorkScheduleResponse.model_validate(schedule)


@router.post("", response_model=WorkScheduleResponse, status_code=201)
async def create_schedule(
    body: WorkScheduleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create/update own work schedule."""
    current = await get_current_schedule(db, user.id)
    if current and current.valid_until is None:
        if body.valid_from <= current.valid_from:
            # Same or earlier start date: update the existing schedule in place
            current.valid_from = body.valid_from
            current.valid_until = body.valid_until
            current.monday_minutes = body.monday_minutes
            current.tuesday_minutes = body.tuesday_minutes
            current.wednesday_minutes = body.wednesday_minutes
            current.thursday_minutes = body.thursday_minutes
            current.friday_minutes = body.friday_minutes
            current.saturday_minutes = body.saturday_minutes
            current.sunday_minutes = body.sunday_minutes
            db.add(current)
            await db.flush()
            return WorkScheduleResponse.model_validate(current)
        else:
            # New start date is later: close the old schedule
            from datetime import timedelta
            current.valid_until = body.valid_from - timedelta(days=1)
            db.add(current)

    schedule = WorkSchedule(
        user_id=user.id,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        monday_minutes=body.monday_minutes,
        tuesday_minutes=body.tuesday_minutes,
        wednesday_minutes=body.wednesday_minutes,
        thursday_minutes=body.thursday_minutes,
        friday_minutes=body.friday_minutes,
        saturday_minutes=body.saturday_minutes,
        sunday_minutes=body.sunday_minutes,
    )
    db.add(schedule)
    await db.flush()
    return WorkScheduleResponse.model_validate(schedule)


@router.put("/user/{user_id}", response_model=WorkScheduleResponse)
async def set_user_schedule(
    user_id: uuid.UUID,
    body: WorkScheduleCreate,
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Set a user's work schedule (admin/boss only)."""
    await check_department_access(user, user_id, db)

    current = await get_current_schedule(db, user_id)
    if current and current.valid_until is None:
        if body.valid_from <= current.valid_from:
            # Same or earlier start date: update the existing schedule in place
            current.valid_from = body.valid_from
            current.valid_until = body.valid_until
            current.monday_minutes = body.monday_minutes
            current.tuesday_minutes = body.tuesday_minutes
            current.wednesday_minutes = body.wednesday_minutes
            current.thursday_minutes = body.thursday_minutes
            current.friday_minutes = body.friday_minutes
            current.saturday_minutes = body.saturday_minutes
            current.sunday_minutes = body.sunday_minutes
            db.add(current)
            await db.flush()
            return WorkScheduleResponse.model_validate(current)
        else:
            # New start date is later: close the old schedule
            from datetime import timedelta
            current.valid_until = body.valid_from - timedelta(days=1)
            db.add(current)

    schedule = WorkSchedule(
        user_id=user_id,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        monday_minutes=body.monday_minutes,
        tuesday_minutes=body.tuesday_minutes,
        wednesday_minutes=body.wednesday_minutes,
        thursday_minutes=body.thursday_minutes,
        friday_minutes=body.friday_minutes,
        saturday_minutes=body.saturday_minutes,
        sunday_minutes=body.sunday_minutes,
    )
    db.add(schedule)
    await db.flush()
    return WorkScheduleResponse.model_validate(schedule)
