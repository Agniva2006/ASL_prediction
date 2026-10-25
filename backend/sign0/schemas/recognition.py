"""Pydantic Landmark Recognition & Model Inference Schemas."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class LandmarkInput(BaseModel):
    """Normalized 63-dimensional MediaPipe hand landmarks (21 joints x [x, y, z])."""
    landmarks: List[float] = Field(..., min_length=63, max_length=63)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: Optional[float] = None


class BatchLandmarkInput(BaseModel):
    batch: List[List[float]] = Field(..., min_length=1, max_length=64)


class TemporalLandmarkInput(BaseModel):
    """16-frame sliding sequence of 63-dimensional landmark coordinates."""
    sequence: List[List[float]] = Field(..., min_length=16, max_length=16)


class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None
    inference_time_ms: float
    model_version: str = "v5.0.0-onnx"


class TemporalPredictionResponse(BaseModel):
    gesture: str
    confidence: float
    probabilities: Dict[str, float]
    frame_count: int = 16
    inference_time_ms: float
