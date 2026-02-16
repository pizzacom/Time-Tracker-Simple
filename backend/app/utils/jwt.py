"""JWT token generation and verification."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """Create a short-lived access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[uuid.UUID]:
    """Extract user ID from a valid token."""
    payload = decode_token(token)
    if payload and "sub" in payload:
        return uuid.UUID(payload["sub"])
    return None
