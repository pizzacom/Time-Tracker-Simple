"""Personal data export/import routes (user's own data as JSON)."""
import uuid
from datetime import date, time, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.models.absence import Absence
from app.models.overtime import OvertimeLedger
from app.middleware.auth import get_current_user, require_admin_or_leader, check_department_access
from app.utils.time_calc import calculate_work_minutes
from app.services.audit_service import log_action

router = APIRouter(prefix="/data", tags=["Personal Data"])


# ---------- Schemas for import ----------

class EntryImport(BaseModel):
    date: date
    start_time: time
    end_time: time
    break_minutes: int = 0
    description: Optional[str] = None


class AbsenceImport(BaseModel):
    date: date
    type: str = Field(..., pattern="^(urlaub|krank|sonderurlaub)$")
    note: Optional[str] = None


class PersonalDataImport(BaseModel):
    entries: list[EntryImport] = []
    absences: list[AbsenceImport] = []


# ---------- Export ----------

async def _build_export(db: AsyncSession, target_user: User) -> dict:
    """Build the personal data export dict for a given user."""
    # Entries
    result = await db.execute(
        select(TimeEntry)
        .where(TimeEntry.user_id == target_user.id)
        .order_by(TimeEntry.date, TimeEntry.start_time)
    )
    entries = []
    for e in result.scalars().all():
        entries.append({
            "date": e.date.isoformat(),
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "break_minutes": e.break_minutes,
            "description": e.description,
            "work_minutes": e.work_minutes,
            "entry_type": e.entry_type,
        })

    # Absences
    result = await db.execute(
        select(Absence)
        .where(Absence.user_id == target_user.id)
        .order_by(Absence.date)
    )
    absences = []
    for a in result.scalars().all():
        absences.append({
            "date": a.date.isoformat(),
            "type": a.type,
            "note": a.note,
        })

    # Overtime history
    result = await db.execute(
        select(OvertimeLedger)
        .where(OvertimeLedger.user_id == target_user.id)
        .order_by(OvertimeLedger.date)
    )
    overtime = []
    for o in result.scalars().all():
        overtime.append({
            "date": o.date.isoformat(),
            "minutes": o.minutes,
            "reason": o.reason,
            "note": o.note,
        })

    return {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "email": target_user.email,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
        },
        "entries": entries,
        "absences": absences,
        "overtime": overtime,
    }


@router.get("/export")
async def export_personal_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export own personal data (entries, absences, overtime) as JSON."""
    return await _build_export(db, user)


@router.get("/export/{user_id}")
async def export_user_data(
    user_id: uuid.UUID,
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Export a user's data as JSON (admin/leader only)."""
    await check_department_access(user, user_id, db)

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return await _build_export(db, target_user)


# ---------- Import ----------

async def _do_import(
    db: AsyncSession,
    target_user_id: uuid.UUID,
    body: PersonalDataImport,
    mode: str,
) -> dict:
    """Core import logic shared by own-import and admin/leader import."""
    counts = {"entries_imported": 0, "entries_skipped": 0,
              "absences_imported": 0, "absences_skipped": 0}

    if mode == "replace":
        existing_entries = await db.execute(
            select(TimeEntry).where(TimeEntry.user_id == target_user_id)
        )
        for e in existing_entries.scalars().all():
            await db.delete(e)

        existing_absences = await db.execute(
            select(Absence).where(Absence.user_id == target_user_id)
        )
        for a in existing_absences.scalars().all():
            await db.delete(a)
        await db.flush()

    for entry_data in body.entries:
        if mode == "merge":
            existing = await db.execute(
                select(TimeEntry).where(
                    and_(
                        TimeEntry.user_id == target_user_id,
                        TimeEntry.date == entry_data.date,
                        TimeEntry.start_time == entry_data.start_time,
                    )
                )
            )
            if existing.scalar_one_or_none():
                counts["entries_skipped"] += 1
                continue

        work_minutes = calculate_work_minutes(
            entry_data.start_time, entry_data.end_time, entry_data.break_minutes
        )
        if work_minutes <= 0:
            counts["entries_skipped"] += 1
            continue

        entry = TimeEntry(
            user_id=target_user_id,
            date=entry_data.date,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            break_minutes=entry_data.break_minutes,
            description=entry_data.description,
            work_minutes=work_minutes,
            entry_type="regular",
        )
        db.add(entry)
        counts["entries_imported"] += 1

    for absence_data in body.absences:
        if mode == "merge":
            existing = await db.execute(
                select(Absence).where(
                    and_(
                        Absence.user_id == target_user_id,
                        Absence.date == absence_data.date,
                        Absence.type == absence_data.type,
                    )
                )
            )
            if existing.scalar_one_or_none():
                counts["absences_skipped"] += 1
                continue

        absence = Absence(
            user_id=target_user_id,
            date=absence_data.date,
            type=absence_data.type,
            note=absence_data.note,
        )
        db.add(absence)
        counts["absences_imported"] += 1

    await db.flush()
    return counts


@router.post("/import")
async def import_personal_data(
    body: PersonalDataImport,
    mode: str = "merge",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import personal entries and absences from JSON.

    mode=merge  (default) – skip entries with same date+start_time
    mode=replace – delete all existing data first, then insert
    """
    if mode not in ("merge", "replace"):
        raise HTTPException(status_code=400, detail="mode must be 'merge' or 'replace'")

    counts = await _do_import(db, user.id, body, mode)

    await log_action(
        db, action="data.import", user_id=user.id, target_type="personal_data",
        details=f"mode={mode}, entries={counts['entries_imported']}, absences={counts['absences_imported']}",
    )

    return {
        "message": f"Imported {counts['entries_imported']} entries and {counts['absences_imported']} absences",
        **counts,
    }


@router.post("/import/{user_id}")
async def import_user_data(
    user_id: uuid.UUID,
    body: PersonalDataImport,
    mode: str = "merge",
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Import data for another user (admin/leader only)."""
    if mode not in ("merge", "replace"):
        raise HTTPException(status_code=400, detail="mode must be 'merge' or 'replace'")

    await check_department_access(user, user_id, db)

    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    counts = await _do_import(db, user_id, body, mode)

    await log_action(
        db, action="data.import", user_id=user.id, target_type="personal_data",
        target_id=str(user_id),
        details=f"mode={mode}, entries={counts['entries_imported']}, absences={counts['absences_imported']}",
    )

    return {
        "message": f"Imported {counts['entries_imported']} entries and {counts['absences_imported']} absences",
        **counts,
    }
