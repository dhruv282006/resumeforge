"""Authentication service handling registration, login, and user state."""

from __future__ import annotations

import uuid
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.profile import Profile
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister


class AuthService:
    """Service encapsulating user authentication and account lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, payload: UserRegister) -> Tuple[User, str]:
        """Register a new user, create their master profile, and issue a token."""
        email_clean = str(payload.email).lower().strip()

        # Check existing user
        query = select(User).where(User.email == email_clean)
        result = await self.session.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        new_user = User(
            id=uuid.uuid4(),
            email=email_clean,
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
            role="user",
            is_active=True,
            onboarding_completed=False,
        )
        self.session.add(new_user)

        # Initialize Master Profile for new user
        new_profile = Profile(
            id=uuid.uuid4(),
            user_id=new_user.id,
            full_name=payload.full_name.strip(),
            email=email_clean,
        )
        self.session.add(new_profile)

        await self.session.commit()
        await self.session.refresh(new_user)

        token = create_access_token(new_user.id)
        return new_user, token

    async def login(self, payload: UserLogin) -> Tuple[User, str]:
        """Verify user credentials and issue an access token."""
        email_clean = str(payload.email).lower().strip()

        query = select(User).where(User.email == email_clean)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )

        token = create_access_token(user.id)
        return user, token

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieve user by UUID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_onboarding(self, user_id: uuid.UUID, completed: bool = True) -> User:
        """Update onboarding status for the given user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.onboarding_completed = completed
        await self.session.commit()
        await self.session.refresh(user)
        return user
