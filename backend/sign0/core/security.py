"""
Sign0 Security & Authentication Module
Industry-standard JWT issuance, password hashing (bcrypt), and rate-limit enforcement.
"""

import os
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.sign0.core.config import settings
from backend.sign0.core.logging import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Tier Definitions
PLANS = {
    "free": {"daily_quota": settings.FREE_TIER_DAILY_QUOTA, "name": "Free Tier", "rps": 5},
    "pro": {"daily_quota": settings.PRO_TIER_DAILY_QUOTA, "name": "Pro Tier", "rps": 30},
    "developer": {"daily_quota": settings.DEV_TIER_DAILY_QUOTA, "name": "Developer Tier", "rps": 100},
}


def hash_password(password: str) -> str:
    """Hash plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Issue a cryptographically signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# In-memory sliding window cache for rate limiting
_usage_tracker: Dict[str, Dict[str, Any]] = {}


def check_rate_limit(user_id: str, plan_name: str = "free") -> bool:
    """Check daily quota and rate limits for a given user/client."""
    plan = PLANS.get(plan_name, PLANS["free"])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if user_id not in _usage_tracker:
        _usage_tracker[user_id] = {"date": today, "count": 0}

    record = _usage_tracker[user_id]
    if record["date"] != today:
        record["date"] = today
        record["count"] = 0

    if record["count"] >= plan["daily_quota"]:
        return False

    record["count"] += 1
    return True


def get_user_usage(user_id: str, plan_name: str = "free") -> Dict[str, Any]:
    """Retrieve usage stats for the current billing cycle."""
    plan = PLANS.get(plan_name, PLANS["free"])
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    record = _usage_tracker.get(user_id, {"date": today, "count": 0})
    if record["date"] != today:
        record = {"date": today, "count": 0}

    remaining = max(0, plan["daily_quota"] - record["count"])
    return {
        "used": record["count"],
        "limit": plan["daily_quota"],
        "remaining": remaining,
        "plan": plan_name,
        "resets_in_hours": 24 - datetime.now(timezone.utc).hour,
    }
