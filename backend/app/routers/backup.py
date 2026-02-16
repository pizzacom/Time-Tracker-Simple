"""Database backup and restore routes (admin only)."""
import io
import json
import uuid
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.models.department import Department
from app.models.time_entry import TimeEntry
from app.models.overtime import OvertimeLedger
from app.models.absence import Absence
from app.models.holiday import Holiday
from app.models.work_schedule import WorkSchedule
from app.models.vacation_budget import VacationBudget
from app.models.setting import Setting
from app.models.audit_log import AuditLog
from app.models.timer_state import TimerState
from app.services.audit_service import log_action

router = APIRouter(prefix="/backup", tags=["Backup & Restore"])

# ── Serialisation helpers ────────────────────────────────────────────

def _serialise(obj) -> str:
    """JSON-safe serialiser for date/time/uuid."""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Cannot serialise {type(obj)}")


# Table export order (respects FK dependencies)
_TABLE_ORDER = [
    ("departments", Department),
    ("users", User),
    ("holidays", Holiday),
    ("settings", Setting),
    ("work_schedules", WorkSchedule),
    ("time_entries", TimeEntry),
    ("overtime_ledger", OvertimeLedger),
    ("absences", Absence),
    ("vacation_budgets", VacationBudget),
    ("audit_logs", AuditLog),
    ("timer_states", TimerState),
]


def _row_to_dict(row) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict."""
    d = {}
    for col in row.__table__.columns:
        val = getattr(row, col.key)
        if isinstance(val, (uuid.UUID,)):
            val = str(val)
        elif isinstance(val, (datetime,)):
            val = val.isoformat()
        elif isinstance(val, date):
            val = val.isoformat()
        elif isinstance(val, time):
            val = val.isoformat()
        d[col.key] = val
    return d


# ── Export endpoint ──────────────────────────────────────────────────

@router.get("/export")
async def export_backup(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Export the entire database as a JSON file (admin only).

    The JSON contains all tables in order, suitable for full restore.
    """
    backup: dict[str, list[dict]] = {}

    for table_name, model in _TABLE_ORDER:
        result = await db.execute(select(model))
        rows = result.scalars().all()
        backup[table_name] = [_row_to_dict(r) for r in rows]

    payload = json.dumps(
        {"version": "1.0", "exported_at": datetime.now(timezone.utc).isoformat(), "tables": backup},
        default=_serialise,
        ensure_ascii=False,
        indent=2,
    )

    await log_action(
        db, action="backup.export", user_id=admin.id,
        details=f"Exported {sum(len(v) for v in backup.values())} rows",
    )
    await db.commit()

    return StreamingResponse(
        io.BytesIO(payload.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=zeittracker_backup.json"},
    )


# ── Import / Restore endpoint ───────────────────────────────────────

@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restore the database from a previously exported JSON backup (admin only).

    **WARNING**: This replaces ALL existing data.
    The import truncates every table and re-inserts from the backup file.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json backup files are accepted")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if "tables" not in data:
        raise HTTPException(status_code=400, detail="Invalid backup format: missing 'tables' key")

    tables_data = data["tables"]

    # Validate expected keys
    expected_tables = {name for name, _ in _TABLE_ORDER}
    provided_tables = set(tables_data.keys())
    missing = expected_tables - provided_tables
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Backup is missing tables: {', '.join(sorted(missing))}",
        )

    # Delete all existing data in reverse FK order
    try:
        # Break circular FK first
        await db.execute(text("UPDATE departments SET leader_id = NULL"))
        for table_name, model in reversed(_TABLE_ORDER):
            await db.execute(model.__table__.delete())
        await db.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {e}")

    # Re-insert data in FK order
    total_rows = 0
    current_table = ""
    try:
        for table_name, model in _TABLE_ORDER:
            current_table = table_name
            rows = tables_data.get(table_name, [])
            for row_data in rows:
                # Convert string UUIDs, dates, times back to native types
                _convert_types(model, row_data)
                await db.execute(model.__table__.insert().values(**row_data))
                total_rows += 1
        await db.flush()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore data for '{current_table}': {e}",
        )

    # Log the restore action (after data is restored)
    await log_action(
        db, action="backup.import", user_id=admin.id,
        details=f"Restored {total_rows} rows from backup",
    )

    return {"message": f"Backup restored successfully ({total_rows} rows)"}


def _convert_types(model, data: dict):
    """Convert JSON string values back to Python types based on column definitions."""
    from sqlalchemy import DateTime, Date, Time
    from sqlalchemy.dialects.postgresql import UUID as pgUUID

    for col in model.__table__.columns:
        key = col.key
        if key not in data or data[key] is None:
            continue

        col_type = type(col.type)
        val = data[key]

        if col_type is pgUUID or (hasattr(col.type, 'impl') and hasattr(col.type, 'as_uuid')):
            if isinstance(val, str):
                data[key] = uuid.UUID(val)
        elif col_type is DateTime:
            if isinstance(val, str):
                data[key] = datetime.fromisoformat(val)
        elif col_type is Date:
            if isinstance(val, str):
                data[key] = date.fromisoformat(val)
        elif col_type is Time:
            if isinstance(val, str):
                data[key] = time.fromisoformat(val)
