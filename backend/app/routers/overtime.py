"""Overtime routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.time_entry import TimeEntry
from app.models.overtime import OvertimeLedger
from app.schemas.overtime import OvertimeUseRequest, OvertimeLedgerResponse, OvertimeBalanceResponse
from app.middleware.auth import get_current_user, require_admin_or_leader, check_department_access
from app.services.overtime_service import (
    get_overtime_balance, get_overtime_history,
    record_overtime_used,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/overtime", tags=["Overtime"])


@router.get("/balance", response_model=OvertimeBalanceResponse)
async def get_my_balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own overtime balance."""
    balance = await get_overtime_balance(db, user.id)
    history = await get_overtime_history(db, user.id)
    return OvertimeBalanceResponse(
        user_id=user.id,
        balance_minutes=balance,
        history=[OvertimeLedgerResponse.model_validate(h) for h in history],
    )


@router.get("/history", response_model=list[OvertimeLedgerResponse])
async def get_my_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own overtime history."""
    history = await get_overtime_history(db, user.id)
    return [OvertimeLedgerResponse.model_validate(h) for h in history]


@router.post("/use")
async def use_overtime(
    body: OvertimeUseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Use overtime to cover a day."""
    balance = await get_overtime_balance(db, user.id)

    if balance < body.minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient overtime balance. Current: {balance} min, Requested: {body.minutes} min",
        )

    # Create an overtime_used time entry for the day
    entry = TimeEntry(
        user_id=user.id,
        date=body.date,
        start_time=__import__("datetime").time(0, 0),
        end_time=__import__("datetime").time(0, 0),
        break_minutes=0,
        description=body.note or "Überstunden eingelöst",
        work_minutes=body.minutes,
        entry_type="overtime_used",
    )
    db.add(entry)
    await db.flush()

    # Record usage in ledger
    await record_overtime_used(
        db, user.id, body.date, body.minutes,
        related_entry_id=entry.id,
        note=body.note,
    )

    await log_action(
        db, action="overtime.use", user_id=user.id, target_type="overtime",
        target_id=str(entry.id), details=f"date={body.date}, minutes={body.minutes}",
    )

    new_balance = await get_overtime_balance(db, user.id)
    return {
        "message": f"Applied {body.minutes} min overtime",
        "new_balance_minutes": new_balance,
    }


@router.delete("/{ledger_id}")
async def delete_overtime_entry(
    ledger_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an overtime ledger entry (e.g. undo a used overtime)."""
    from sqlalchemy import select as sel

    result = await db.execute(
        sel(OvertimeLedger).where(
            OvertimeLedger.id == ledger_id,
            OvertimeLedger.user_id == user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Overtime entry not found")

    # If this was a 'used' entry, also delete the related overtime_used TimeEntry
    if entry.reason == "used" and entry.related_time_entry_id:
        te_result = await db.execute(
            sel(TimeEntry).where(TimeEntry.id == entry.related_time_entry_id)
        )
        te = te_result.scalar_one_or_none()
        if te:
            await db.delete(te)

    await db.delete(entry)
    await db.flush()

    await log_action(
        db, action="overtime.delete", user_id=user.id, target_type="overtime",
        target_id=str(ledger_id), details=f"Deleted {entry.reason} entry ({entry.minutes} min)",
    )

    new_balance = await get_overtime_balance(db, user.id)
    return {"message": "Overtime entry deleted", "new_balance_minutes": new_balance}


@router.get("/user/{user_id}", response_model=OvertimeBalanceResponse)
async def get_user_balance(
    user_id: uuid.UUID,
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's overtime balance (admin/boss only)."""
    await check_department_access(user, user_id, db)

    balance = await get_overtime_balance(db, user_id)
    history = await get_overtime_history(db, user_id)
    return OvertimeBalanceResponse(
        user_id=user_id,
        balance_minutes=balance,
        history=[OvertimeLedgerResponse.model_validate(h) for h in history],
    )
