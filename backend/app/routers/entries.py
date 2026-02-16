"""Time entry routes."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.schemas.entry import EntryCreate, EntryUpdate, EntryResponse
from app.utils.time_calc import calculate_work_minutes
from app.middleware.auth import get_current_user, require_admin_or_leader, check_department_access
from app.services.overtime_service import record_overtime_earned
from app.services.work_schedule_service import get_soll_minutes_for_date
from app.services.audit_service import log_action

router = APIRouter(prefix="/entries", tags=["Time Entries"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=list[EntryResponse])
async def get_entries(
    date_from: date = Query(None),
    date_to: date = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own time entries with optional date filter."""
    query = select(TimeEntry).where(TimeEntry.user_id == user.id)
    if date_from:
        query = query.where(TimeEntry.date >= date_from)
    if date_to:
        query = query.where(TimeEntry.date <= date_to)
    query = query.order_by(TimeEntry.date.desc(), TimeEntry.start_time)

    result = await db.execute(query)
    return [EntryResponse.model_validate(e) for e in result.scalars().all()]


@router.post("", response_model=EntryResponse, status_code=201)
@limiter.limit("100/day")
async def create_entry(
    request: Request,
    body: EntryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new time entry."""
    work_minutes = calculate_work_minutes(body.start_time, body.end_time, body.break_minutes)

    if work_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Work time must be positive. Check start/end times and break duration.",
        )

    entry = TimeEntry(
        user_id=user.id,
        date=body.date,
        start_time=body.start_time,
        end_time=body.end_time,
        break_minutes=body.break_minutes,
        description=body.description,
        work_minutes=work_minutes,
        entry_type="regular",
    )
    db.add(entry)
    await db.flush()

    await log_action(
        db, action="entry.create", user_id=user.id, target_type="entry",
        target_id=str(entry.id), details=f"date={body.date}, work={work_minutes}min",
    )

    # Calculate overtime for this day
    await _update_daily_overtime(db, user.id, body.date)

    return EntryResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=EntryResponse)
async def update_entry(
    entry_id: uuid.UUID,
    body: EntryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update own time entry."""
    result = await db.execute(
        select(TimeEntry).where(
            and_(TimeEntry.id == entry_id, TimeEntry.user_id == user.id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Time entry {entry_id} not found or does not belong to your account")

    if body.date is not None:
        entry.date = body.date
    if body.start_time is not None:
        entry.start_time = body.start_time
    if body.end_time is not None:
        entry.end_time = body.end_time
    if body.break_minutes is not None:
        entry.break_minutes = body.break_minutes
    if body.description is not None:
        entry.description = body.description

    entry.work_minutes = calculate_work_minutes(
        entry.start_time, entry.end_time, entry.break_minutes
    )

    db.add(entry)
    await db.flush()

    await log_action(
        db, action="entry.update", user_id=user.id, target_type="entry",
        target_id=str(entry.id), details=f"date={entry.date}, work={entry.work_minutes}min",
    )

    # Recalculate overtime for affected day
    await _update_daily_overtime(db, user.id, entry.date)

    return EntryResponse.model_validate(entry)


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete own time entry."""
    result = await db.execute(
        select(TimeEntry).where(
            and_(TimeEntry.id == entry_id, TimeEntry.user_id == user.id)
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail=f"Time entry {entry_id} not found or does not belong to your account")

    entry_date = entry.date
    await log_action(
        db, action="entry.delete", user_id=user.id, target_type="entry",
        target_id=str(entry_id), details=f"date={entry_date}",
    )
    await db.delete(entry)
    await db.flush()

    # Recalculate overtime for affected day
    await _update_daily_overtime(db, user.id, entry_date)

    return {"message": "Entry deleted"}


@router.get("/user/{user_id}", response_model=list[EntryResponse])
async def get_user_entries(
    user_id: uuid.UUID,
    date_from: date = Query(None),
    date_to: date = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get entries for a specific user (admin/boss only)."""
    await check_department_access(user, user_id, db)

    query = select(TimeEntry).where(TimeEntry.user_id == user_id)
    if date_from:
        query = query.where(TimeEntry.date >= date_from)
    if date_to:
        query = query.where(TimeEntry.date <= date_to)
    query = query.order_by(TimeEntry.date.desc(), TimeEntry.start_time)

    result = await db.execute(query)
    return [EntryResponse.model_validate(e) for e in result.scalars().all()]


async def _update_daily_overtime(db: AsyncSession, user_id: uuid.UUID, entry_date: date):
    """Recalculate and update overtime for a specific day.
    
    This removes existing 'earned' ledger entries for the day and creates
    a new one if Ist > Soll.
    """
    from app.models.overtime import OvertimeLedger

    # Delete existing earned entries for this day
    existing = await db.execute(
        select(OvertimeLedger).where(
            and_(
                OvertimeLedger.user_id == user_id,
                OvertimeLedger.date == entry_date,
                OvertimeLedger.reason == "earned",
            )
        )
    )
    for ot in existing.scalars().all():
        await db.delete(ot)

    # Calculate Soll and Ist
    soll = await get_soll_minutes_for_date(db, user_id, entry_date)
    
    ist_result = await db.execute(
        select(func.coalesce(func.sum(TimeEntry.work_minutes), 0)).where(
            and_(
                TimeEntry.user_id == user_id,
                TimeEntry.date == entry_date,
                TimeEntry.entry_type == "regular",
            )
        )
    )
    ist = ist_result.scalar()

    # If Ist > Soll, record earned overtime
    delta = ist - soll
    if delta > 0:
        await record_overtime_earned(db, user_id, entry_date, delta)
