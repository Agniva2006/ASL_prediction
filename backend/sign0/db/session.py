"""
Sign0 Database Engine and Session Factory
Manages SQLite/PostgreSQL connections with connection pooling and scoped sessions.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.sign0.core.config import settings

# Ensure data directory exists
data_dir = Path(settings.DATA_DIR)
data_dir.mkdir(parents=True, exist_ok=True)

db_url = os.getenv("DATABASE_URL", f"sqlite:///{settings.DB_PATH}")

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
