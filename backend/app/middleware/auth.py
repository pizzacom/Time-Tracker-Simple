"""Authentication middleware and dependencies."""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the access token."""
    token = None

    # Try Bearer token from Authorization header
    if credentials:
        token = credentials.credentials

    # Try from cookie as fallback
    if not token and request:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: No access token found in Authorization header or cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token — please login again",
        )

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the current user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_admin_or_leader(user: User = Depends(get_current_user)) -> User:
    """Require admin or Abteilungsleiter role."""
    if user.role not in ("admin", "abteilungsleiter"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Abteilungsleiter access required",
        )
    return user


async def check_department_access(
    user: User, target_user_id: uuid.UUID, db: AsyncSession
) -> bool:
    """Check if an Abteilungsleiter has access to a target user's data."""
    if user.role == "admin":
        return True

    if user.role == "abteilungsleiter":
        # Get target user
        result = await db.execute(select(User).where(User.id == target_user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail=f"Target user {target_user_id} not found")
        # Check if target user is in the same department
        if target_user.department_id == user.department_id and user.department_id is not None:
            return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this user's data",
    )
