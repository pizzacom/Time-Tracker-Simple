"""Absence and vacation routes."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.absence import Absence
from app.models.vacation_budget import VacationBudget
from app.schemas.absence import AbsenceCreate, AbsenceResponse, VacationBudgetResponse, VacationBudgetUpdate
from app.middleware.auth import get_current_user, require_admin, require_admin_or_leader, check_department_access
from app.config import settings

router = APIRouter(prefix="/absences", tags=["Absences"])


@router.get("", response_model=list[AbsenceResponse])
async def get_my_absences(
    year: int = Query(None),
    type: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own absences."""
    query = select(Absence).where(Absence.user_id == user.id)
    if year:
        from datetime import date as date_type
        query = query.where(
            and_(
                Absence.date >= date_type(year, 1, 1),
                Absence.date <= date_type(year, 12, 31),
            )
        )
    if type:
        query = query.where(Absence.type == type)
    query = query.order_by(Absence.date.desc())

    result = await db.execute(query)
    return [AbsenceResponse.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AbsenceResponse, status_code=201)
async def create_absence(
    body: AbsenceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a day as absent."""
    # Check if absence already exists for this date
    existing = await db.execute(
        select(Absence).where(
            and_(Absence.user_id == user.id, Absence.date == body.date)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Absence already exists for this date",
        )

    absence = Absence(
        user_id=user.id,
        date=body.date,
        type=body.type,
        note=body.note,
    )
    db.add(absence)
    await db.flush()

    # Update vacation budget if type is urlaub
    if body.type == "urlaub":
        await _update_vacation_used(db, user.id, body.date.year)

    return AbsenceResponse.model_validate(absence)


@router.delete("/{absence_id}")
async def delete_absence(
    absence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove own absence."""
    result = await db.execute(
        select(Absence).where(
            and_(Absence.id == absence_id, Absence.user_id == user.id)
        )
    )
    absence = result.scalar_one_or_none()
    if not absence:
        raise HTTPException(status_code=404, detail=f"Absence {absence_id} not found or does not belong to your account")

    year = absence.date.year
    was_urlaub = absence.type == "urlaub"

    await db.delete(absence)
    await db.flush()

    if was_urlaub:
        await _update_vacation_used(db, user.id, year)

    return {"message": "Absence removed"}


@router.get("/user/{user_id}", response_model=list[AbsenceResponse])
async def get_user_absences(
    user_id: uuid.UUID,
    year: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's absences (admin/boss only)."""
    await check_department_access(user, user_id, db)

    query = select(Absence).where(Absence.user_id == user_id)
    if year:
        from datetime import date as date_type
        query = query.where(
            and_(
                Absence.date >= date_type(year, 1, 1),
                Absence.date <= date_type(year, 12, 31),
            )
        )
    query = query.order_by(Absence.date.desc())

    result = await db.execute(query)
    return [AbsenceResponse.model_validate(a) for a in result.scalars().all()]


# Vacation budget endpoints

@router.get("/vacation-budget", response_model=VacationBudgetResponse)
async def get_my_vacation_budget(
    year: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own vacation budget."""
    if not year:
        year = date.today().year

    budget = await _get_or_create_budget(db, user.id, year)
    return VacationBudgetResponse(
        user_id=user.id,
        year=year,
        total_days=budget.total_days,
        used_days=budget.used_days,
        remaining_days=budget.remaining_days,
    )


@router.put("/vacation-budget/{user_id}", response_model=VacationBudgetResponse)
async def set_vacation_budget(
    user_id: uuid.UUID,
    body: VacationBudgetUpdate,
    year: int = Query(None),
    current_user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Set vacation budget for a user (admin or leader for own dept)."""
    if current_user.role == "abteilungsleiter":
        await check_department_access(current_user, user_id, db)
    if not year:
        year = date.today().year

    budget = await _get_or_create_budget(db, user_id, year)
    budget.total_days = body.total_days
    db.add(budget)
    await db.flush()

    return VacationBudgetResponse(
        user_id=user_id,
        year=year,
        total_days=budget.total_days,
        used_days=budget.used_days,
        remaining_days=budget.remaining_days,
    )


async def _get_or_create_budget(db: AsyncSession, user_id: uuid.UUID, year: int) -> VacationBudget:
    """Get or create a vacation budget for a user/year."""
    result = await db.execute(
        select(VacationBudget).where(
            and_(VacationBudget.user_id == user_id, VacationBudget.year == year)
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        budget = VacationBudget(
            user_id=user_id,
            year=year,
            total_days=settings.DEFAULT_VACATION_DAYS,
            used_days=0,
        )
        db.add(budget)
        await db.flush()
    return budget


async def _update_vacation_used(db: AsyncSession, user_id: uuid.UUID, year: int):
    """Recalculate used vacation days from absences."""
    from datetime import date as date_type
    count_result = await db.execute(
        select(func.count()).select_from(Absence).where(
            and_(
                Absence.user_id == user_id,
                Absence.type == "urlaub",
                Absence.date >= date_type(year, 1, 1),
                Absence.date <= date_type(year, 12, 31),
            )
        )
    )
    used = count_result.scalar() or 0

    budget = await _get_or_create_budget(db, user_id, year)
    budget.used_days = used
    db.add(budget)
