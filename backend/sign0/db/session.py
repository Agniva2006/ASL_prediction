"""
Sign0 Database Engine — Dual-Layer Strategy
- Prisma (prisma-client-py)  : Primary async ORM for PostgreSQL. All new code uses this.
- SQLAlchemy                 : Legacy sync layer kept for FastAPI background tasks and
                               compatibility with any existing sync dependencies.
                               Falls back to SQLite when DATABASE_URL is not set.

PostgreSQL URL format:
    postgresql+asyncpg://user:pass@host:5432/dbname   (Prisma / asyncpg)
    postgresql://user:pass@host:5432/dbname           (SQLAlchemy sync)
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.sign0.core.config import settings

# ── SQLAlchemy sync engine (fallback / legacy) ──────────────────────────────
_data_dir = Path(settings.DATA_DIR)
_data_dir.mkdir(parents=True, exist_ok=True)

# Prefer DATABASE_URL from env; strip +asyncpg driver tag for sync SQLAlchemy
_raw_url: str = os.getenv("DATABASE_URL", f"sqlite:///{settings.DB_PATH}")

# SQLAlchemy needs `postgresql://` not `postgresql+asyncpg://`
_sync_url = _raw_url.replace("postgresql+asyncpg://", "postgresql://")

_connect_args: dict = {"check_same_thread": False} if "sqlite" in _sync_url else {}

engine = create_engine(
    _sync_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a synchronous SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
