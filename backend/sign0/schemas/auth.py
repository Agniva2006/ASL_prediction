"""Pydantic Auth & User Schemas."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    plan: str
    api_key: Optional[str] = None
    created_at: Optional[datetime] = None


class UsageResponse(BaseModel):
    username: str
    plan: str
    daily_used: int
    daily_limit: int
    daily_remaining: int
    resets_in_hours: int
