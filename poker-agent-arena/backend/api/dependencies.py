"""Common API dependencies."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status

from config import get_settings
from db.database import get_db
from services.redis_service import RedisService, get_redis
from sqlalchemy.ext.asyncio import AsyncSession
from websocket.auth import get_session_from_token


# Database dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_redis_service() -> RedisService:
    """Get Redis service instance."""
    return RedisService(get_redis())


RedisServiceDep = Annotated[RedisService, Depends(get_redis_service)]


async def get_current_user(
    authorization: str | None = Header(None),
) -> dict:
    """
    Get current authenticated user from session token.

    Raises HTTPException 401 if not authenticated.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = parts[1]
    session = await get_session_from_token(token)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    return session


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def get_optional_user(
    authorization: str | None = Header(None),
) -> dict | None:
    """
    Get current user if authenticated, None otherwise.

    Does not raise exception for unauthenticated requests.
    """
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        return await get_session_from_token(token)
    except Exception:
        return None


OptionalUser = Annotated[Optional[dict], Depends(get_optional_user)]


async def require_admin(
    user: CurrentUser,
) -> dict:
    """
    Require admin privileges.

    Raises HTTPException 403 if user is not admin.
    """
    if not user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user


AdminUser = Annotated[dict, Depends(require_admin)]
