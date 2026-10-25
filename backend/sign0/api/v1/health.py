"""
Sign0 Health Diagnostics & Telemetry API Router (v1)
Endpoints:
- GET /health/live: Kubernetes liveness probe
- GET /health/ready: Kubernetes readiness probe (checks model loading and DB)
- GET /metrics: Prometheus metrics exposition endpoint
"""

from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.sign0.core.config import settings
from backend.sign0.core.metrics import metrics
from backend.sign0.services.inference_service import inference_engine
from backend.sign0.db.session import get_db

router = APIRouter(tags=["Health & Telemetry"])


@router.get("/health/live")
@router.get("/healthz")
@router.get("/health")
def liveness_probe():
    """Liveness probe verifying HTTP daemon is answering requests."""
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/health/ready")
def readiness_probe(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity and ONNX model sessions."""
    # Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check Models
    mlp_loaded = inference_engine.mlp_session is not None
    transformer_loaded = inference_engine.transformer_session is not None

    all_ready = db_ok and mlp_loaded

    return {
        "status": "ready" if all_ready else "degraded",
        "database_connected": db_ok,
        "mlp_onnx_loaded": mlp_loaded,
        "transformer_onnx_loaded": transformer_loaded,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }


@router.get("/metrics")
def prometheus_metrics():
    """Exposes real-time Prometheus telemetry metrics for scraping."""
    content = metrics.to_prometheus_format()
    return Response(content=content, media_type="text/plain; version=0.0.4")
