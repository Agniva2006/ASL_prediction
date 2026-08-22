from sqlalchemy import Column, Integer, String, JSON, DateTime
from backend.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="learner")
    plan = Column(String, default="free")
    api_key = Column(String, nullable=True)
    
    # Billing fields
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, nullable=True)
    
    # Simple JSON column for usage to keep it close to original structure
    # In a full normalized DB, usage would be its own table
    usage = Column(JSON, default={})
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    endpoint = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
