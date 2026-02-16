"""Holiday management routes."""
import uuid
from datetime import date as date_type, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.holiday import Holiday
from app.schemas.holiday import HolidayCreate, HolidayResponse
from app.middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/holidays", tags=["Holidays"])


def _easter_sunday(year: int) -> date_type:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date_type(year, month, day)


def _german_holidays(year: int) -> list[tuple[date_type, str]]:
    """Calculate all German public holidays for a year."""
    easter = _easter_sunday(year)
    holidays = [
        (date_type(year, 1, 1), "Neujahr"),
        (date_type(year, 5, 1), "Tag der Arbeit"),
        (date_type(year, 10, 3), "Tag der Deutschen Einheit"),
        (date_type(year, 12, 25), "1. Weihnachtsfeiertag"),
        (date_type(year, 12, 26), "2. Weihnachtsfeiertag"),
        # Easter-based movable holidays
        (easter - timedelta(days=2), "Karfreitag"),
        (easter + timedelta(days=1), "Ostermontag"),
        (easter + timedelta(days=39), "Christi Himmelfahrt"),
        (easter + timedelta(days=50), "Pfingstmontag"),
    ]
    return sorted(holidays, key=lambda x: x[0])


@router.get("", response_model=list[HolidayResponse])
async def get_holidays(
    year: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get holidays for a year."""
    from datetime import date
    if not year:
        year = date.today().year

    result = await db.execute(
        select(Holiday)
        .where(
            and_(
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
        )
        .order_by(Holiday.date)
    )
    return [HolidayResponse.model_validate(h) for h in result.scalars().all()]


@router.post("", response_model=HolidayResponse, status_code=201)
async def create_holiday(
    body: HolidayCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a holiday (admin only)."""
    existing = await db.execute(
        select(Holiday).where(Holiday.date == body.date)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Holiday already exists for this date",
        )

    holiday = Holiday(
        date=body.date,
        name=body.name,
        is_half_day=body.is_half_day,
        region=body.region,
    )
    db.add(holiday)
    await db.flush()
    return HolidayResponse.model_validate(holiday)


@router.delete("/{holiday_id}")
async def delete_holiday(
    holiday_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a holiday (admin only)."""
    result = await db.execute(select(Holiday).where(Holiday.id == holiday_id))
    holiday = result.scalar_one_or_none()
    if not holiday:
        raise HTTPException(status_code=404, detail=f"Holiday {holiday_id} not found")

    await db.delete(holiday)
    return {"message": "Holiday removed"}


@router.post("/auto-generate", response_model=list[HolidayResponse], status_code=201)
async def auto_generate_holidays(
    year: int = Query(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate German public holidays for a year (admin only)."""
    generated = []
    for hdate, hname in _german_holidays(year):
        # Skip if already exists
        existing = await db.execute(
            select(Holiday).where(Holiday.date == hdate)
        )
        if existing.scalar_one_or_none():
            continue

        holiday = Holiday(
            date=hdate,
            name=hname,
            is_half_day=False,
            region="DE",
        )
        db.add(holiday)
        await db.flush()
        generated.append(HolidayResponse.model_validate(holiday))

    return generated
