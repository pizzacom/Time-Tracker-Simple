"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, RefreshResponse, UserResponse, ChangePasswordRequest
from app.utils.password import verify_password, hash_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.middleware.auth import get_current_user
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    # Audit log
    await log_action(
        db, action="user.login", user_id=user.id, target_type="user",
        target_id=str(user.id), ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh the access token using the refresh token cookie."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token cookie found — please login again",
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token — please login again",
        )

    import uuid
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/api/v1/auth",
    )

    return RefreshResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout and clear refresh token cookie."""
    await log_action(
        db, action="user.logout", user_id=user.id, target_type="user",
        target_id=str(user.id), ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return {"message": "Logged out"}


@router.post("/change-password")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters",
        )

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password",
        )

    user.password_hash = hash_password(body.new_password)
    db.add(user)
    await log_action(
        db, action="user.change_password", user_id=user.id, target_type="user",
        target_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Password changed successfully"}
