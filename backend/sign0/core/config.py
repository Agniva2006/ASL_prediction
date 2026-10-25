"""
Sign0 Enterprise Configuration & Environment Settings
Industry-grade configuration using Pydantic BaseSettings with full validation.
"""

import os
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "Sign0 AI Engine & Low-Bandwidth Neural Codec"
    APP_VERSION: str = "5.0.0"
    ENVIRONMENT: str = Field(default=os.getenv("ENVIRONMENT", "production"))
    DEBUG: bool = Field(default=os.getenv("DEBUG", "false").lower() in ("true", "1"))

    # ── Server Binding ─────────────────────────────────────────────────────
    HOST: str = Field(default=os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default=int(os.getenv("PORT", "8000")))

    # ── Security & Auth ────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default=os.getenv(
            "SIGN0_SECRET_KEY",
            "d8c2e0b5f1a3e87d4c99e21b7a0f6c5e3d8a1b2c4e5f60718293a4b5c6d7e8f9"
        )
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "https://asl-prediction.vercel.app",
        "https://asl-prediction-v2.onrender.com",
        "*",
    ]

    # ── Database (PostgreSQL via Prisma / SQLAlchemy) ──────────────────────
    # Prisma uses the asyncpg driver format:
    #   postgresql+asyncpg://user:pass@host:5432/dbname
    # SQLAlchemy sync layer strips the +asyncpg prefix automatically.
    DATABASE_URL: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://sign0:sign0pass@localhost:5432/sign0db"
        )
    )

    # ── Stripe Billing ─────────────────────────────────────────────────────
    STRIPE_API_KEY: str = Field(default=os.getenv("STRIPE_API_KEY", ""))
    STRIPE_WEBHOOK_SECRET: str = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    STRIPE_PRICE_PRO: str = Field(default=os.getenv("STRIPE_PRICE_PRO", "price_sign0_pro_monthly"))
    STRIPE_PRICE_DEVELOPER: str = Field(default=os.getenv("STRIPE_PRICE_DEVELOPER", "price_sign0_dev_monthly"))

    # ── Rate Limiting & Quotas ─────────────────────────────────────────────
    FREE_TIER_DAILY_QUOTA: int = 150
    PRO_TIER_DAILY_QUOTA: int = 5000
    DEV_TIER_DAILY_QUOTA: int = 100000

    # ── File Paths (ML artefacts, SQLite fallback) ─────────────────────────
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    # SQLite path — used only if DATABASE_URL is not set / points to sqlite
    DB_PATH: str = os.path.join(DATA_DIR, "sign0.db")

    # ── Neural Codec Parameters ────────────────────────────────────────────
    CODEC_PAYLOAD_BYTES: int = 48
    LATENT_COMPONENTS: int = 9
    SAMPLING_RATE_HZ: int = 30


# Global singleton
settings = Settings()
