"""
Sign0 Prisma Async Client Manager
Provides a single shared Prisma client instance with connection lifecycle management.
Import `db` anywhere in the app to get the ready-to-use async Prisma client.

Usage in FastAPI endpoint:
    from backend.sign0.db.prisma_client import db
    user = await db.user.find_unique(where={"username": username})
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from prisma import Prisma
from backend.sign0.core.logging import logger


class PrismaManager:
    """Singleton async Prisma client with connect/disconnect lifecycle."""

    def __init__(self):
        self._client: Prisma | None = None

    @property
    def client(self) -> Prisma:
        if self._client is None:
            raise RuntimeError(
                "Prisma client is not connected. "
                "Call await prisma_manager.connect() before using the client. "
                "If using FastAPI, ensure the lifespan manager is configured."
            )
        return self._client

    async def connect(self):
        """Open the database connection pool."""
        if self._client is None:
            self._client = Prisma()
        if not self._client.is_connected():
            await self._client.connect()
            logger.info("Prisma PostgreSQL client connected")

    async def disconnect(self):
        """Close the database connection pool."""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            logger.info("Prisma PostgreSQL client disconnected")

    def __getattr__(self, name: str):
        """Delegate attribute access to the underlying Prisma client."""
        return getattr(self.client, name)


# Singleton instance — import this anywhere in the app
prisma = PrismaManager()


@asynccontextmanager
async def get_prisma() -> AsyncGenerator[Prisma, None]:
    """
    FastAPI dependency context that yields the connected Prisma client.
    Use with Depends() in route handlers that need explicit client injection.
    """
    yield prisma.client
