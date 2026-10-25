"""
Sign0 Prisma-based User Repository
Thin async data-access layer wrapping Prisma client calls.
All user creation, lookup, and update operations go through here.
"""

from __future__ import annotations
import secrets
from typing import Optional

from prisma.models import User as PrismaUser
from backend.sign0.db.prisma_client import prisma
from backend.sign0.core.security import hash_password
from backend.sign0.core.logging import logger


class UserRepository:
    """Async repository for User CRUD operations via Prisma."""

    async def find_by_username(self, username: str) -> Optional[PrismaUser]:
        return await prisma.user.find_unique(where={"username": username})

    async def find_by_email(self, email: str) -> Optional[PrismaUser]:
        return await prisma.user.find_unique(where={"email": email})

    async def find_by_username_or_email(
        self, username: str, email: str
    ) -> Optional[PrismaUser]:
        return await prisma.user.find_first(
            where={"OR": [{"username": username}, {"email": email}]}
        )

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "learner",
        plan: str = "free",
    ) -> PrismaUser:
        user = await prisma.user.create(
            data={
                "username": username,
                "email": email,
                "fullName": full_name or username,
                "hashedPassword": hash_password(password),
                "role": role,
                "plan": plan,
                "apiKey": f"sign0_{secrets.token_hex(16)}",
            }
        )
        logger.info(f"Created new user: {username} (plan={plan})")
        return user

    async def update_plan(
        self,
        username: str,
        plan: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        subscription_status: Optional[str] = "active",
    ) -> PrismaUser:
        data: dict = {"plan": plan}
        if stripe_customer_id:
            data["stripeCustomerId"] = stripe_customer_id
        if stripe_subscription_id:
            data["stripeSubscriptionId"] = stripe_subscription_id
        if subscription_status:
            data["subscriptionStatus"] = subscription_status

        user = await prisma.user.update(
            where={"username": username},
            data=data,
        )
        logger.info(f"Updated plan for {username} to {plan}")
        return user

    async def log_activity(
        self,
        username: str,
        endpoint: str,
        method: str = "POST",
        latency_ms: float = 0.0,
        status_code: int = 200,
        user_id: Optional[int] = None,
    ) -> None:
        await prisma.activity.create(
            data={
                "username": username,
                "endpoint": endpoint,
                "method": method,
                "latencyMs": latency_ms,
                "statusCode": status_code,
                **({"userId": user_id} if user_id else {}),
            }
        )


user_repo = UserRepository()
