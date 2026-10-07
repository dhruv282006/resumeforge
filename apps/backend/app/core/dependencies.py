"""Application dependencies for auth and user resolution."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.profile_service import DEFAULT_USER_ID, ProfileService


async def get_current_user_id(
    authorization: Optional[str] = Header(None),
) -> uuid.UUID:
    """Extract authenticated user ID from Authorization header.

    If no authorization header is provided, falls back to DEFAULT_USER_ID
    for backward compatibility with automated tests and legacy endpoints.
    If an authorization header is provided but invalid/expired, raises 401.
    """
    if not authorization:
        return DEFAULT_USER_ID

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token expired or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch the active user model instance for the resolved user ID."""
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        # For default test user, get or create transparently
        profile_service = ProfileService(db)
        user = await profile_service.get_or_create_user(user_id)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )
    return user
