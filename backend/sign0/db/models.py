"""
Sign0 SQLAlchemy Domain Models: User, Activity, ApiKey, ConversationSession
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from backend.sign0.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    full_name = Column(String(128), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="learner")
    plan = Column(String(32), default="free")
    api_key = Column(String(128), unique=True, index=True, nullable=True)

    # Billing metadata
    stripe_customer_id = Column(String(128), nullable=True)
    stripe_subscription_id = Column(String(128), nullable=True)
    subscription_status = Column(String(64), nullable=True)

    # Quota & Telemetry
    usage = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(64), index=True)
    endpoint = Column(String(128), nullable=False)
    latency_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="activities")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    channel_type = Column(String(32), default="webrtc_datachannel")  # websocket, webrtc, http
    total_frames = Column(Integer, default=0)
    words_transcribed = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
