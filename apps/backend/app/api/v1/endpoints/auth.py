"""Endpoints for User Authentication and Profile Lifecycle."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    OnboardingStatusUpdate,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserRegister,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Create a new user account, initialize their master profile, and return an auth token."""
    user, token = await service.register(payload)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain access token",
)
async def login(
    payload: UserLogin,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Validate credentials and return access token."""
    user, token = await service.login(payload)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user details and onboarding state",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile and metadata for currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    summary="Invalidate session on client",
)
async def logout() -> dict:
    """Client clears token from secure storage."""
    return {"message": "Logged out successfully"}


@router.post(
    "/onboarding/complete",
    response_model=UserResponse,
    summary="Mark onboarding as completed for current user",
)
async def complete_onboarding(
    payload: OnboardingStatusUpdate = OnboardingStatusUpdate(onboarding_completed=True),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Update onboarding_completed status for current user."""
    user = await service.update_onboarding(current_user.id, completed=payload.onboarding_completed)
    return UserResponse.model_validate(user)
