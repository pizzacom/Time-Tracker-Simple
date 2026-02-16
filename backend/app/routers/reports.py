"""Reports routes."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.models.department import Department
from app.models.holiday import Holiday
from app.models.absence import Absence
from app.models.overtime import OvertimeLedger
from app.schemas.report import MonthlyReport, DayReport, DepartmentOverview, DepartmentOverviewEntry, SystemSummary
from app.middleware.auth import get_current_user, require_admin, require_admin_or_leader, check_department_access
from app.services.work_schedule_service import get_soll_minutes_for_date
from app.services.overtime_service import get_overtime_balance
from app.utils.time_calc import get_month_days, get_weekday_name_de

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _build_monthly_report(
    db: AsyncSession, user_id: uuid.UUID, year: int, month: int
) -> MonthlyReport:
    """Build a complete monthly report for a user."""
    # Get user info
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    days = get_month_days(year, month)

    # Get all entries for the month
    entries_result = await db.execute(
        select(TimeEntry).where(
            and_(
                TimeEntry.user_id == user_id,
                TimeEntry.date >= days[0],
                TimeEntry.date <= days[-1],
            )
        ).order_by(TimeEntry.date, TimeEntry.start_time)
    )
    entries = entries_result.scalars().all()

    # Get holidays
    holidays_result = await db.execute(
        select(Holiday).where(
            and_(Holiday.date >= days[0], Holiday.date <= days[-1])
        )
    )
    holidays = {h.date: h for h in holidays_result.scalars().all()}

    # Get absences
    absences_result = await db.execute(
        select(Absence).where(
            and_(
                Absence.user_id == user_id,
                Absence.date >= days[0],
                Absence.date <= days[-1],
            )
        )
    )
    absences = {a.date: a for a in absences_result.scalars().all()}

    # Build day reports
    day_reports = []
    total_soll = 0
    total_ist = 0
    work_days = 0
    vacation_days = 0
    sick_days = 0

    for d in days:
        # Raw soll = schedule-based hours (ignoring holidays/absences)
        raw_soll = await get_soll_minutes_for_date(db, user_id, d, raw=True)
        day_entries = [e for e in entries if e.date == d]
        ist = sum(e.work_minutes for e in day_entries)
        overtime_used = sum(e.work_minutes for e in day_entries if e.entry_type == "overtime_used")

        is_holiday = d in holidays
        absence = absences.get(d)
        is_absence = absence is not None

        # Credit holidays and absences as worked time equal to schedule soll
        credited_minutes = 0
        if is_holiday and raw_soll > 0:
            holiday_obj = holidays[d]
            credited_minutes = raw_soll  # already halved for half-days by get_soll_minutes_for_date
        if is_absence and raw_soll > 0:
            credited_minutes = raw_soll

        # Use raw_soll as the displayed soll for the day (reflects schedule)
        soll = raw_soll

        # Add credited time to ist (holiday/absence count as "worked")
        ist += credited_minutes

        if absence:
            if absence.type == "urlaub":
                vacation_days += 1
            elif absence.type == "krank":
                sick_days += 1

        if ist > 0:
            work_days += 1

        total_soll += soll
        total_ist += ist

        day_reports.append(DayReport(
            date=d,
            weekday=get_weekday_name_de(d),
            soll_minutes=soll,
            ist_minutes=ist,
            delta_minutes=ist - soll,
            entry_count=len(day_entries),
            is_holiday=is_holiday,
            is_absence=is_absence,
            absence_type=absence.type if absence else None,
            overtime_used_minutes=overtime_used,
            entries=[{
                "id": str(e.id),
                "start_time": e.start_time.strftime("%H:%M"),
                "end_time": e.end_time.strftime("%H:%M"),
                "break_minutes": e.break_minutes,
                "work_minutes": e.work_minutes,
                "entry_type": e.entry_type,
                "description": e.description or "",
            } for e in day_entries],
        ))

    # Get overtime stats
    earned_result = await db.execute(
        select(func.coalesce(func.sum(OvertimeLedger.minutes), 0)).where(
            and_(
                OvertimeLedger.user_id == user_id,
                OvertimeLedger.date >= days[0],
                OvertimeLedger.date <= days[-1],
                OvertimeLedger.reason == "earned",
            )
        )
    )
    overtime_earned = earned_result.scalar()

    used_result = await db.execute(
        select(func.coalesce(func.sum(OvertimeLedger.minutes), 0)).where(
            and_(
                OvertimeLedger.user_id == user_id,
                OvertimeLedger.date >= days[0],
                OvertimeLedger.date <= days[-1],
                OvertimeLedger.reason == "used",
            )
        )
    )
    overtime_used = abs(used_result.scalar())

    balance = await get_overtime_balance(db, user_id)

    return MonthlyReport(
        user_id=user_id,
        user_name=user.full_name,
        year=year,
        month=month,
        soll_total=total_soll,
        ist_total=total_ist,
        delta_total=total_ist - total_soll,
        overtime_earned=overtime_earned,
        overtime_used=overtime_used,
        overtime_balance=balance,
        work_days=work_days,
        vacation_days=vacation_days,
        sick_days=sick_days,
        holiday_count=len(holidays),
        days=day_reports,
    )


@router.get("/monthly", response_model=MonthlyReport)
async def get_my_monthly_report(
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own monthly report."""
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    return await _build_monthly_report(db, user.id, year, month)


@router.get("/monthly/{user_id}", response_model=MonthlyReport)
async def get_user_monthly_report(
    user_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's monthly report (admin/boss only)."""
    await check_department_access(user, user_id, db)

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    return await _build_monthly_report(db, user_id, year, month)


@router.get("/department/{dept_id}", response_model=DepartmentOverview)
async def get_department_overview(
    dept_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get department overview (admin/boss only)."""
    dept_result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = dept_result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department {dept_id} not found")

    if user.role == "abteilungsleiter" and user.department_id != dept_id:
        raise HTTPException(status_code=403, detail=f"Access denied: Leaders can only view reports for their own department (yours: {user.department_id}, requested: {dept_id})")

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    # Get all members
    members_result = await db.execute(
        select(User).where(
            and_(User.department_id == dept_id, User.is_active == True)
        )
    )
    members = members_result.scalars().all()

    days = get_month_days(year, month)
    member_entries = []

    # Pre-fetch absences and holidays for all members
    dept_holidays_result = await db.execute(
        select(Holiday).where(
            and_(Holiday.date >= days[0], Holiday.date <= days[-1])
        )
    )
    dept_holidays = {h.date: h for h in dept_holidays_result.scalars().all()}

    for member in members:
        # Get absences for this member
        member_absences_result = await db.execute(
            select(Absence).where(
                and_(
                    Absence.user_id == member.id,
                    Absence.date >= days[0],
                    Absence.date <= days[-1],
                )
            )
        )
        member_absences = {a.date: a for a in member_absences_result.scalars().all()}

        # Get Soll total (raw schedule-based) and credited time for holidays/absences
        total_soll = 0
        total_credited = 0
        for d in days:
            raw_soll = await get_soll_minutes_for_date(db, member.id, d, raw=True)
            total_soll += raw_soll
            if (d in dept_holidays or d in member_absences) and raw_soll > 0:
                total_credited += raw_soll

        # Get Ist total
        ist_result = await db.execute(
            select(func.coalesce(func.sum(TimeEntry.work_minutes), 0)).where(
                and_(
                    TimeEntry.user_id == member.id,
                    TimeEntry.date >= days[0],
                    TimeEntry.date <= days[-1],
                )
            )
        )
        total_ist = ist_result.scalar() + total_credited

        balance = await get_overtime_balance(db, member.id)

        # Get vacation remaining
        from app.routers.absences import _get_or_create_budget
        budget = await _get_or_create_budget(db, member.id, year)

        member_entries.append(DepartmentOverviewEntry(
            user_id=member.id,
            user_name=member.full_name,
            soll_total=total_soll,
            ist_total=total_ist,
            delta_total=total_ist - total_soll,
            overtime_balance=balance,
            vacation_days_remaining=budget.remaining_days,
        ))

    return DepartmentOverview(
        department_id=dept_id,
        department_name=dept.name,
        year=year,
        month=month,
        members=member_entries,
    )


@router.get("/summary", response_model=SystemSummary)
async def get_system_summary(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide summary (admin only)."""
    today = date.today()
    days = get_month_days(today.year, today.month)

    users_count = (await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)
    )).scalar()

    depts_count = (await db.execute(
        select(func.count()).select_from(Department)
    )).scalar()

    entries_count = (await db.execute(
        select(func.count()).select_from(TimeEntry)
    )).scalar()

    month_ist = (await db.execute(
        select(func.coalesce(func.sum(TimeEntry.work_minutes), 0)).where(
            and_(TimeEntry.date >= days[0], TimeEntry.date <= days[-1])
        )
    )).scalar()

    overtime_total = (await db.execute(
        select(func.coalesce(func.sum(OvertimeLedger.minutes), 0))
    )).scalar()

    return SystemSummary(
        total_users=users_count,
        total_departments=depts_count,
        total_entries=entries_count,
        current_month_ist=month_ist,
        current_month_soll=0,  # Would need per-user calc
        total_overtime_balance=overtime_total,
    )
