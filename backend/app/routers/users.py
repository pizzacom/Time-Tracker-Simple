"""User management routes."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.schemas.user import (
    UserCreate, UserUpdate, UserProfileUpdate, UserResponse, UserWithBalance,
)
from app.utils.password import hash_password
from app.middleware.auth import get_current_user, require_admin, require_admin_or_leader
from app.services.overtime_service import get_overtime_balance
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserWithBalance)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile with overtime balance."""
    balance = await get_overtime_balance(db, user.id)
    dept_name = None
    if user.department_id:
        dept_result = await db.execute(
            select(Department.name).where(Department.id == user.department_id)
        )
        dept_name = dept_result.scalar_one_or_none()

    return UserWithBalance(
        **{**UserResponse.model_validate(user).model_dump(), 'department_name': dept_name},
        overtime_balance_minutes=balance,
    )


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update own profile."""
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    db.add(user)
    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserResponse])
async def list_users(
    role: str = Query(None),
    is_active: bool = Query(None),
    department_id: uuid.UUID = Query(None),
    user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """List users (admin: all, leader: own department only)."""
    query = select(User).outerjoin(Department, User.department_id == Department.id)
    if user.role == "abteilungsleiter":
        # Leaders can only see their own department
        query = query.where(User.department_id == user.department_id)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if department_id:
        query = query.where(User.department_id == department_id)
    query = query.order_by(Department.name.nulls_last(), User.last_name, User.first_name)

    result = await db.execute(query)
    users = result.scalars().all()

    # Enrich with department names
    dept_ids = {u.department_id for u in users if u.department_id}
    dept_map = {}
    if dept_ids:
        dept_result = await db.execute(select(Department).where(Department.id.in_(dept_ids)))
        dept_map = {d.id: d.name for d in dept_result.scalars().all()}

    responses = []
    for u in users:
        resp = UserResponse.model_validate(u)
        resp.department_name = dept_map.get(u.department_id)
        responses.append(resp)
    return responses


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin or leader for own dept)."""
    # Leaders can only create workers in their own department
    if current_user.role == "abteilungsleiter":
        if body.role != "worker":
            raise HTTPException(status_code=403, detail="Leaders can only create workers")
        if body.department_id and body.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Can only add to own department")
        body.department_id = current_user.department_id

    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        department_id=body.department_id,
    )
    db.add(user)
    await db.flush()

    # Create default work schedule (Mon-Fri 480 min = 8h, Sat/Sun 0)
    from datetime import date as date_type
    from app.models.work_schedule import WorkSchedule
    default_schedule = WorkSchedule(
        user_id=user.id,
        valid_from=date_type(2020, 1, 1),
        monday_minutes=480,
        tuesday_minutes=480,
        wednesday_minutes=480,
        thursday_minutes=480,
        friday_minutes=480,
        saturday_minutes=0,
        sunday_minutes=0,
    )
    db.add(default_schedule)
    await db.flush()

    await log_action(
        db, action="user.create", user_id=current_user.id, target_type="user",
        target_id=str(user.id), details=f"email={user.email}, role={user.role}",
    )
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: User = Depends(require_admin_or_leader),
    db: AsyncSession = Depends(get_db),
):
    """Update a user (admin or leader for own dept)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    # Leaders: can only edit users in their department, no role changes
    if current_user.role == "abteilungsleiter":
        if user.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Can only edit users in your department")
        if body.role is not None:
            raise HTTPException(status_code=403, detail="Leaders cannot change roles")
        if body.department_id is not None and body.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Cannot move users to other departments")

    if body.email is not None:
        # Check email uniqueness
        existing = await db.execute(
            select(User).where(User.email == body.email, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user.email = body.email
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.role is not None:
        user.role = body.role
    if body.department_id is not None:
        user.department_id = body.department_id
    if body.is_active is not None:
        user.is_active = body.is_active

    db.add(user)
    await log_action(
        db, action="user.update", user_id=current_user.id, target_type="user",
        target_id=str(user.id), details=str(body.model_dump(exclude_unset=True)),
    )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    user.is_active = False
    db.add(user)
    await log_action(
        db, action="user.deactivate", user_id=admin.id, target_type="user",
        target_id=str(user.id), details=f"email={user.email}",
    )
    return {"message": "User deactivated"}


@router.delete("/{user_id}/permanent")
async def permanently_delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a user and all associated data (admin only).

    This cascades to time_entries, work_schedules, overtime_entries,
    absences, vacation_budgets, and audit_log entries.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    email = user.email
    user_id_str = str(user.id)

    await db.delete(user)
    await db.flush()

    await log_action(
        db, action="user.hard_delete", user_id=admin.id, target_type="user",
        target_id=user_id_str, details=f"email={email} (permanently deleted)",
    )
    return {"message": "User permanently deleted"}
