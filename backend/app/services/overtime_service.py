"""Overtime service - manages earning, using, and balance calculations."""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.overtime import OvertimeLedger
from app.models.time_entry import TimeEntry


async def get_overtime_balance(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Get the current overtime balance in minutes for a user."""
    result = await db.execute(
        select(func.coalesce(func.sum(OvertimeLedger.minutes), 0))
        .where(OvertimeLedger.user_id == user_id)
    )
    return result.scalar()


async def get_overtime_history(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 100
):
    """Get overtime ledger entries for a user."""
    result = await db.execute(
        select(OvertimeLedger)
        .where(OvertimeLedger.user_id == user_id)
        .order_by(OvertimeLedger.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def record_overtime_earned(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_date: date,
    minutes: int,
    related_entry_id: Optional[uuid.UUID] = None,
    note: Optional[str] = None,
):
    """Record earned overtime (positive minutes)."""
    entry = OvertimeLedger(
        user_id=user_id,
        date=entry_date,
        minutes=abs(minutes),
        reason="earned",
        related_time_entry_id=related_entry_id,
        note=note or f"Earned {abs(minutes)} min overtime",
    )
    db.add(entry)
    return entry


async def record_overtime_used(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_date: date,
    minutes: int,
    related_entry_id: Optional[uuid.UUID] = None,
    note: Optional[str] = None,
):
    """Record used overtime (negative minutes)."""
    entry = OvertimeLedger(
        user_id=user_id,
        date=entry_date,
        minutes=-abs(minutes),
        reason="used",
        related_time_entry_id=related_entry_id,
        note=note or f"Used {abs(minutes)} min overtime",
    )
    db.add(entry)
    return entry


async def record_overtime_adjustment(
    db: AsyncSession,
    user_id: uuid.UUID,
    entry_date: date,
    minutes: int,
    note: Optional[str] = None,
):
    """Record an admin adjustment (can be positive or negative)."""
    entry = OvertimeLedger(
        user_id=user_id,
        date=entry_date,
        minutes=minutes,
        reason="adjustment",
        note=note or f"Manual adjustment: {minutes} min",
    )
    db.add(entry)
    return entry
