"""
Sign0 Prediction API Router (v1)
Endpoints: /predict, /predict/mlp, /predict/int8, /predict/transformer
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.sign0.schemas.recognition import (
    LandmarkInput,
    PredictionResponse,
    TemporalLandmarkInput,
    TemporalPredictionResponse,
)
from backend.sign0.services.inference_service import inference_engine
from backend.sign0.core.security import check_rate_limit
from backend.sign0.api.v1.auth import get_optional_user_dependency
from backend.sign0.db.models import User

router = APIRouter(prefix="/predict", tags=["Model Inference"])


@router.post("", response_model=PredictionResponse)
@router.post("/mlp", response_model=PredictionResponse)
def predict_static_landmarks(
    req: LandmarkInput,
    current_user: Optional[User] = Depends(get_optional_user_dependency),
):
    """
    Sub-millisecond static ASL sign recognition.
    Accepts 63 MediaPipe 3D coordinates (21 hand joints x [x, y, z]).
    """
    client_id = current_user.username if current_user else "guest_client"
    plan_name = current_user.plan if current_user else "free"

    if not check_rate_limit(client_id, plan_name):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily quota exceeded. Please upgrade your subscription.",
        )

    result = inference_engine.predict_mlp(req.landmarks, use_int8=False)
    return result


@router.post("/int8", response_model=PredictionResponse)
def predict_quantized_landmarks(
    req: LandmarkInput,
    current_user: Optional[User] = Depends(get_optional_user_dependency),
):
    """
    Ultra-low latency INT8 quantized inference accelerated via CPU SIMD (AVX-512).
    """
    client_id = current_user.username if current_user else "guest_client"
    plan_name = current_user.plan if current_user else "free"

    if not check_rate_limit(client_id, plan_name):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily quota exceeded.",
        )

    result = inference_engine.predict_mlp(req.landmarks, use_int8=True)
    return result


@router.post("/transformer", response_model=TemporalPredictionResponse)
def predict_temporal_sequence(
    req: TemporalLandmarkInput,
    current_user: Optional[User] = Depends(get_optional_user_dependency),
):
    """
    Dynamic 16-frame gesture classification using Spatial-Temporal Multi-Head Self-Attention.
    Distinguishes phrases like 'HELLO', 'THANK_YOU', 'PLEASE', 'EMERGENCY', 'PAIN'.
    """
    client_id = current_user.username if current_user else "guest_client"
    plan_name = current_user.plan if current_user else "free"

    if not check_rate_limit(client_id, plan_name):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily quota exceeded.",
        )

    result = inference_engine.predict_transformer(req.sequence)
    return result
