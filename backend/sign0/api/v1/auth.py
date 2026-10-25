"""
Sign0 Auth API Router (v1)
Endpoints: /signup, /login, /me, /usage, /plans, /change-plan
"""

import secrets
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from backend.sign0.core.config import settings
from backend.sign0.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    check_rate_limit,
    get_user_usage,
    PLANS,
    oauth2_scheme,
)
from backend.sign0.db.session import get_db
from backend.sign0.db.models import User, Activity
from backend.sign0.schemas.auth import UserRegister, UserLogin, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["Authentication & Quotas"])


def get_current_user_dependency(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency for authenticating requests via JWT Bearer token."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def get_optional_user_dependency(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional authentication for endpoints that allow guest access."""
    try:
        return get_current_user_dependency(authorization=authorization, token=token, db=db)
    except HTTPException:
        return None


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account and return signed JWT."""
    existing_user = (
        db.query(User).filter((User.username == req.username) | (User.email == req.email)).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered.")

    new_user = User(
        username=req.username,
        email=req.email,
        full_name=req.full_name or req.username,
        hashed_password=hash_password(req.password),
        role="learner",
        plan="free",
        api_key=f"sign0_{secrets.token_hex(16)}",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "role": new_user.role, "plan": new_user.plan})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "plan": new_user.plan,
            "api_key": new_user.api_key,
        },
    }


@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with username/password and receive JWT access token."""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.username, "role": user.role, "plan": user.plan})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "plan": user.plan,
            "api_key": user.api_key,
        },
    }


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user_dependency)):
    """Fetch current user session info and active plan."""
    usage = get_user_usage(current_user.username, current_user.plan)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "plan": current_user.plan,
        "api_key": current_user.api_key,
        "usage": usage,
    }


@router.get("/usage")
def get_usage_metrics(current_user: User = Depends(get_current_user_dependency)):
    """Retrieve daily rate limit quota and remaining queries."""
    return get_user_usage(current_user.username, current_user.plan)


@router.get("/plans")
def list_available_plans():
    """Return available subscription tiers and feature matrices."""
    return PLANS
