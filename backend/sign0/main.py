"""
Sign0 Main Application — Updated with Prisma lifespan
Connects Prisma on startup, disconnects on shutdown.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.sign0.core.config import settings
from backend.sign0.core.logging import logger
from backend.sign0.db.session import engine, Base
from backend.sign0.db.prisma_client import prisma
from backend.sign0.api.v1.router import api_v1_router
from backend.sign0.api.v1.auth import router as compat_auth_router
from backend.sign0.api.v1.predict import router as compat_predict_router
from backend.sign0.api.v1.stream import router as compat_stream_router
from backend.sign0.api.v1.synthesis import router as compat_synthesis_router
from backend.sign0.api.v1.payment import router as compat_payment_router
from backend.sign0.api.v1.health import router as compat_health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown — initialises Prisma + SQLAlchemy."""
    # SQLAlchemy: create tables for legacy sync layer
    logger.info("Creating SQLAlchemy database tables (fallback layer)...")
    Base.metadata.create_all(bind=engine)

    # Prisma: open async PostgreSQL connection pool
    logger.info("Connecting Prisma client to PostgreSQL...")
    await prisma.connect()

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} ready.")
    yield

    # Shutdown
    await prisma.disconnect()
    logger.info("Sign0 application shut down cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-grade AI Sign Language Platform — "
        "48-Byte Neural Latent Codec, DDPM Synthesizer, PostgreSQL + Prisma."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Limit", "X-RateLimit-Reset"],
)

# Versioned routes
app.include_router(api_v1_router)

# Backward-compatible root aliases (consumed by existing static frontend)
app.include_router(compat_auth_router)
app.include_router(compat_predict_router)
app.include_router(compat_stream_router)
app.include_router(compat_synthesis_router)
app.include_router(compat_payment_router)
app.include_router(compat_health_router)


@app.get("/", tags=["Root"])
def root_status():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_v1_docs": "/docs",
        "health_check": "/health/ready",
        "metrics_endpoint": "/metrics",
    }
