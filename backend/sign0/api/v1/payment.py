"""
Sign0 Stripe Billing & Payment Processor (v1)
Supports Stripe Checkout sessions, Customer Portals, and secure Webhook event processing with sandbox fallback.
"""

import os
import secrets
import stripe
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Depends, Header, status
from sqlalchemy.orm import Session

from backend.sign0.core.config import settings
from backend.sign0.core.logging import logger
from backend.sign0.core.security import PLANS
from backend.sign0.api.v1.auth import get_current_user_dependency
from backend.sign0.db.session import get_db
from backend.sign0.db.models import User, Activity
from backend.sign0.schemas.billing import CheckoutRequest, CheckoutResponse, CustomerPortalResponse

router = APIRouter(prefix="/payment", tags=["Billing & Payments"])

is_sandbox = not bool(settings.STRIPE_API_KEY)
if not is_sandbox:
    stripe.api_key = settings.STRIPE_API_KEY


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Initiate a Stripe Checkout session or return sandbox instant-upgrade mock."""
    plan = req.plan.lower().strip()
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan.")

    if is_sandbox:
        # Instant upgrade for sandbox testing
        current_user.plan = plan
        db.commit()
        return {
            "checkout_url": f"/frontend/home.html?billing_success=true&plan={plan}",
            "session_id": f"cs_test_sandbox_{secrets.token_hex(8)}",
            "mode": "sandbox",
        }

    price_id = settings.STRIPE_PRICE_PRO if plan == "pro" else settings.STRIPE_PRICE_DEVELOPER
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=req.success_url or "https://asl-prediction.vercel.app/home.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url or "https://asl-prediction.vercel.app/home.html?cancelled=true",
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            metadata={"username": current_user.username, "plan": plan},
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "mode": "live",
        }
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal", response_model=CustomerPortalResponse)
def create_customer_portal(
    current_user: User = Depends(get_current_user_dependency),
):
    """Direct subscriber to Stripe Customer Portal to manage cards and cancellations."""
    if is_sandbox or not current_user.stripe_customer_id:
        return {"portal_url": "/frontend/home.html?portal_sandbox=true"}

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="https://asl-prediction.vercel.app/home.html",
        )
        return {"portal_url": session.url}
    except Exception as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook_listener(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Process cryptographically verified Stripe webhook events (invoice.paid, subscription.deleted)."""
    if is_sandbox:
        return {"status": "ignored", "reason": "sandbox_mode"}

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Webhook signature error: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        username = data_object.get("metadata", {}).get("username")
        plan = data_object.get("metadata", {}).get("plan", "pro")
        customer_id = data_object.get("customer")
        if username:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.plan = plan
                user.stripe_customer_id = customer_id
                db.commit()
                logger.info(f"Upgraded user {username} to {plan}")

    return {"status": "success"}
