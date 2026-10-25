"""
Sign0 v1 Master API Router
Combines Auth, Prediction, Streaming, Synthesis, Payment, and Health sub-routers.
"""

from fastapi import APIRouter

from backend.sign0.api.v1.auth import router as auth_router
from backend.sign0.api.v1.predict import router as predict_router
from backend.sign0.api.v1.stream import router as stream_router
from backend.sign0.api.v1.synthesis import router as synthesis_router
from backend.sign0.api.v1.payment import router as payment_router
from backend.sign0.api.v1.health import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(predict_router)
api_v1_router.include_router(stream_router)
api_v1_router.include_router(synthesis_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(health_router)

__all__ = ["api_v1_router"]
