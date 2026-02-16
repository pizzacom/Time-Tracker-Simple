"""Audit logging service — records sensitive operations."""
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Write an audit log entry.

    Args:
        db: Database session (should be the same session as the calling transaction).
        action: Short action identifier, e.g. "user.login", "user.create", "entry.delete".
        user_id: The user who performed the action.
        target_type: Entity kind affected, e.g. "user", "entry", "holiday".
        target_id: Primary key (stringified UUID) of the affected entity.
        details: Free-form JSON or text with additional context.
        ip_address: Client IP address.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    # Don't flush/commit here — let the caller's session handle it.
