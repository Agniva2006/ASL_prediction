"""
backend/auth.py — Sign0 AI Engine Authentication & Plan Authorization
JWT-based authentication with bcrypt hashing, rate limiting, and subscription plan definitions.
"""

import os
import time
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

# Read stable JWT secret from environment or local file
SECRET_KEY = os.environ.get("SIGN0_SECRET_KEY", "").strip()
if not SECRET_KEY:
    _SECRET_FILE = Path(__file__).resolve().parent / "data" / ".jwt_secret"
    _SECRET_FILE.parent.mkdir(exist_ok=True, parents=True)
    if _SECRET_FILE.exists():
        SECRET_KEY = _SECRET_FILE.read_text().strip()
    else:
        SECRET_KEY = secrets.token_hex(32)
        try:
            _SECRET_FILE.write_text(SECRET_KEY)
        except Exception:
            pass  # read-only disk fallback

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days (remember-me session)

# ──────────────────────────────────────────────
# Subscription Plans
# ──────────────────────────────────────────────

PLANS: Dict[str, dict] = {
    "free": {
        "name": "Free",
        "price": 0,
        "price_label": "$0/month",
        "daily_quota": 20,
        "monthly_quota": 200,
        "features": {
            "static_mlp": True,
            "sequence_transformer": False,
            "diffusion_synthesizer": False,
            "dict_visualizer": False,
            "tts": True,
            "custom_recorder": False,
        },
        "description": "Basic sign recognition for learning & testing.",
        "highlights": [
            "20 static predictions per day",
            "Real-time MediaPipe visual feedback",
            "Text-to-Speech audio reader",
            "Basic alphabetical dictionary cards",
        ]
    },
    "pro": {
        "name": "Pro Learner",
        "price": 9,
        "price_label": "$9/month",
        "daily_quota": 500,
        "monthly_quota": 5000,
        "features": {
            "static_mlp": True,
            "sequence_transformer": True,
            "diffusion_synthesizer": False,
            "dict_visualizer": True,
            "tts": True,
            "custom_recorder": False,
        },
        "description": "Ideal for students and speech-impaired individuals.",
        "highlights": [
            "500 predictions per day",
            "Spatial-Temporal Transformer (seq) access",
            "Interactive 3D sign visual dictionary player",
            "WebRTC camera feed calibration",
            "Gamified practice challenge modes",
        ]
    },
    "developer": {
        "name": "Developer / Enterprise",
        "price": 49,
        "price_label": "$49/month",
        "daily_quota": 999999,  # Unlimited
        "monthly_quota": 999999,
        "features": {
            "static_mlp": True,
            "sequence_transformer": True,
            "diffusion_synthesizer": True,
            "dict_visualizer": True,
            "tts": True,
            "custom_recorder": True,
        },
        "description": "Unlimited API access for developers and research labs.",
        "highlights": [
            "Unlimited requests (no daily quotas)",
            "Text-to-Sign DDPM Diffusion Synthesizer access",
            "Interactive custom gesture recording",
            "Private API Key provisioning",
            "Commercial integration rights",
        ]
    }
}

# ──────────────────────────────────────────────
# Passwords & JWT Cryptography
# ──────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ──────────────────────────────────────────────
# User Database Helpers (JSON)
# ──────────────────────────────────────────────

USER_DB_DIR = Path(__file__).resolve().parent / "data"
USER_DB_PATH = USER_DB_DIR / "users_db.json"

def load_users() -> dict:
    USER_DB_DIR.mkdir(exist_ok=True, parents=True)
    if not USER_DB_PATH.exists():
        # Seed default developer account
        default_db = {
            "dev_demo": {
                "password": hash_password("asldemo2026"),
                "email": "demo@sign0.ai",
                "full_name": "Demo Developer",
                "role": "developer",
                "plan": "developer",
                "api_key": "sign0_live_dev_k8s_9281aef10",
                "created_at": "2026-08-13T00:00:00Z",
                "usage_daily": {},
                "usage_monthly": {},
                "activity": [],
                "sessions": []
            }
        }
        with open(USER_DB_PATH, "w") as f:
            json.dump(default_db, f, indent=2)
        return default_db
    try:
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    USER_DB_DIR.mkdir(exist_ok=True, parents=True)
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)

# ──────────────────────────────────────────────
# Rate Limiting & Gating
# ──────────────────────────────────────────────

def get_current_date_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def get_current_month_str() -> str:
    return datetime.utcnow().strftime("%Y-%m")

def record_api_call(username: str, endpoint: str):
    users = load_users()
    if username not in users:
        return
    u = users[username]
    day = get_current_date_str()
    month = get_current_month_str()
    
    # Record usage counts
    u.setdefault("usage_daily", {})
    u.setdefault("usage_monthly", {})
    u["usage_daily"][day] = u["usage_daily"].get(day, 0) + 1
    u["usage_monthly"][month] = u["usage_monthly"].get(month, 0) + 1
    
    # Log activity
    activity = u.setdefault("activity", [])
    activity.append({
        "endpoint": endpoint,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    u["activity"] = activity[-50:]  # Keep last 50
    save_users(users)

def get_usage(username: str) -> dict:
    users = load_users()
    u = users.get(username, {})
    day = get_current_date_str()
    month = get_current_month_str()
    
    plan = u.get("plan", "free")
    limits = PLANS.get(plan, PLANS["free"])
    
    queries_today = u.get("usage_daily", {}).get(day, 0)
    queries_month = u.get("usage_monthly", {}).get(month, 0)
    
    daily_quota = limits["daily_quota"]
    monthly_quota = limits["monthly_quota"]
    
    return {
        "plan": plan,
        "queries_today": queries_today,
        "queries_month": queries_month,
        "daily_quota": daily_quota,
        "monthly_quota": monthly_quota,
        "daily_remaining": max(0, daily_quota - queries_today),
        "monthly_remaining": max(0, monthly_quota - queries_month),
    }

def check_rate_limit(username: str) -> int:
    """Returns the remaining requests. Raises HTTP 429 if quota exceeded."""
    usage = get_usage(username)
    if usage["queries_today"] >= usage["daily_quota"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily request quota exceeded. Please upgrade your plan."
        )
    return usage["daily_remaining"]

# ──────────────────────────────────────────────
# FastAPI Dependencies
# ──────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form", auto_error=False)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")
    
    user_data = users[username]
    user_data["username"] = username
    return user_data

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            return None
        users = load_users()
        if username in users:
            u = users[username]
            u["username"] = username
            return u
    except Exception:
        pass
    return None
