"""Department management routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.middleware.auth import get_current_user, require_admin, require_admin_or_leader

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """List departments."""
    if user.role == "admin":
        query = select(Department)
    else:
        # Abteilungsleiter: only their own department
        query = select(Department).where(Department.id == user.department_id)

    result = await db.execute(query.order_by(Department.name))
    departments = result.scalars().all()

    # Get member counts
    responses = []
    for dept in departments:
        count_result = await db.execute(
            select(func.count()).select_from(User)
            .where(User.department_id == dept.id)
        )
        count = count_result.scalar()
        resp = DepartmentResponse(
            id=dept.id,
            name=dept.name,
            leader_id=dept.leader_id,
            created_at=dept.created_at,
            member_count=count,
        )
        responses.append(resp)

    return responses


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    body: DepartmentCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a department (admin only)."""
    existing = await db.execute(
        select(Department).where(Department.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name already exists",
        )

    dept = Department(name=body.name, leader_id=body.leader_id)
    db.add(dept)
    await db.flush()

    return DepartmentResponse(
        id=dept.id, name=dept.name, leader_id=dept.leader_id,
        created_at=dept.created_at, member_count=0,
    )


@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    body: DepartmentUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a department (admin only)."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department {dept_id} not found")

    if body.name is not None:
        dept.name = body.name
    if body.leader_id is not None:
        dept.leader_id = body.leader_id

    db.add(dept)
    await db.flush()

    count_result = await db.execute(
        select(func.count()).select_from(User).where(User.department_id == dept.id)
    )
    count = count_result.scalar()

    return DepartmentResponse(
        id=dept.id, name=dept.name, leader_id=dept.leader_id,
        created_at=dept.created_at, member_count=count,
    )


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a department (admin only, only if no members)."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department {dept_id} not found")

    # Check for members
    count_result = await db.execute(
        select(func.count()).select_from(User).where(User.department_id == dept_id)
    )
    count = count_result.scalar()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete department with {count} member(s). Remove all members first.",
        )

    await db.delete(dept)
    return {"message": "Department deleted"}
