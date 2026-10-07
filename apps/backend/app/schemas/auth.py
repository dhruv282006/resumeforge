"""Schemas for Authentication and User management."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")


class UserRegister(BaseModel):
    """Payload for user registration."""

    email: str = Field(..., min_length=3, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserLogin(BaseModel):
    """Payload for user authentication."""

    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Public user profile response."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str = "user"
    onboarding_completed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Authentication token response with embedded user summary."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OnboardingStatusUpdate(BaseModel):
    """Payload to update onboarding status."""

    onboarding_completed: bool = True
