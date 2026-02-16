"""Work schedule service - resolves Soll-Arbeitszeit for any date."""
import uuid
from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_schedule import WorkSchedule
from app.models.holiday import Holiday
from app.models.absence import Absence


async def get_schedule_for_date(
    db: AsyncSession, user_id: uuid.UUID, target_date: date
) -> WorkSchedule | None:
    """Find the active work schedule for a user on a given date.

    Falls back to the user's earliest schedule if the target date is
    before any schedule's valid_from (i.e. schedule was set up after work
    already started).
    """
    result = await db.execute(
        select(WorkSchedule)
        .where(
            and_(
                WorkSchedule.user_id == user_id,
                WorkSchedule.valid_from <= target_date,
                (WorkSchedule.valid_until.is_(None)) | (WorkSchedule.valid_until >= target_date),
            )
        )
        .order_by(WorkSchedule.valid_from.desc())
        .limit(1)
    )
    schedule = result.scalar_one_or_none()
    if schedule is not None:
        return schedule

    # Fallback: if target_date is before any schedule, use the earliest one
    fallback = await db.execute(
        select(WorkSchedule)
        .where(WorkSchedule.user_id == user_id)
        .order_by(WorkSchedule.valid_from.asc())
        .limit(1)
    )
    return fallback.scalar_one_or_none()


async def get_soll_minutes_for_date(
    db: AsyncSession, user_id: uuid.UUID, target_date: date, *, raw: bool = False
) -> int:
    """Calculate Soll minutes for a user on a specific date.

    When raw=False (default):
        Returns 0 if it's a full-day holiday or the user has an absence.
        This is used for overtime calculations where holidays/absences
        should not count toward required hours.

    When raw=True:
        Returns the schedule-based Soll regardless of holidays/absences.
        Half-day holidays still reduce by half. Used for reports where
        holidays and absences should be credited as working time.
    """
    # Check if holiday
    holiday_result = await db.execute(
        select(Holiday).where(Holiday.date == target_date)
    )
    holiday = holiday_result.scalar_one_or_none()

    if not raw:
        if holiday and not holiday.is_half_day:
            return 0

        # Check if absence
        absence_result = await db.execute(
            select(Absence).where(
                and_(Absence.user_id == user_id, Absence.date == target_date)
            )
        )
        absence = absence_result.scalar_one_or_none()
        if absence:
            return 0

    # Get schedule
    schedule = await get_schedule_for_date(db, user_id, target_date)
    if not schedule:
        return 0

    soll = schedule.get_minutes_for_weekday(target_date.weekday())

    # Half-day holiday: reduce by half
    if holiday and holiday.is_half_day:
        soll = soll // 2

    # Full-day holiday in raw mode: return full soll (don't zero it)
    return soll


async def get_current_schedule(
    db: AsyncSession, user_id: uuid.UUID
) -> WorkSchedule | None:
    """Get the currently active work schedule."""
    from datetime import date as date_type
    return await get_schedule_for_date(db, user_id, date_type.today())
