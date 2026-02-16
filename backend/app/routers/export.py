"""Export routes (PDF, CSV, Excel)."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user, require_admin_or_leader, check_department_access
from app.models.department import Department
from app.services.export_service import generate_pdf, generate_csv, generate_excel, generate_department_excel

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/pdf")
async def export_my_pdf(
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export own monthly PDF."""
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    pdf_bytes = await generate_pdf(db, user.id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}_{user.last_name}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf/{user_id}")
async def export_user_pdf(
    user_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Export a user's monthly PDF (admin/boss only)."""
    await check_department_access(user, user_id, db)

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    pdf_bytes = await generate_pdf(db, user_id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/csv")
async def export_my_csv(
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export own monthly CSV."""
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    csv_bytes = await generate_csv(db, user.id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}_{user.last_name}.csv"

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/csv/{user_id}")
async def export_user_csv(
    user_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Export a user's CSV (admin/boss only)."""
    await check_department_access(user, user_id, db)

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    csv_bytes = await generate_csv(db, user_id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}.csv"

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/excel")
async def export_my_excel(
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export own monthly Excel."""
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    excel_bytes = await generate_excel(db, user.id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}_{user.last_name}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/excel/{user_id}")
async def export_user_excel(
    user_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Export a user's Excel (admin/boss only)."""
    await check_department_access(user, user_id, db)

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    excel_bytes = await generate_excel(db, user_id, year, month)
    filename = f"Zeiterfassung_{year}_{month:02d}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/department/{dept_id}/excel")
async def export_department_excel(
    dept_id: uuid.UUID,
    year: int = Query(None),
    month: int = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Export department Excel with summary + one sheet per worker."""
    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == dept_id)
    )
    dept = dept_result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department {dept_id} not found")

    # Leaders can only export own department
    if user.role == "abteilungsleiter" and user.department_id != dept_id:
        raise HTTPException(status_code=403, detail=f"Access denied: Leaders can only export their own department (yours: {user.department_id}, requested: {dept_id})")

    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month

    excel_bytes = await generate_department_excel(db, dept_id, year, month)
    filename = f"Abteilung_{dept.name}_{year}_{month:02d}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
