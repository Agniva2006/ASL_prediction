"""Pydantic Billing & Subscription Schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    plan: str = Field(..., pattern="^(pro|developer)$")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    mode: str  # live or sandbox


class CustomerPortalResponse(BaseModel):
    portal_url: str


class PlanInfo(BaseModel):
    name: str
    price_usd_monthly: float
    daily_quota: int
    features: list[str]
