"""Pydantic Real-Time Streaming & Codec Schemas."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class StreamFramePacket(BaseModel):
    landmarks: List[float] = Field(..., min_length=63, max_length=63)
    frame_id: int
    timestamp_ms: float


class StreamInferenceResult(BaseModel):
    type: str = "frame_prediction"
    predicted_letter: str
    confidence: float
    is_steady: bool
    hold_frames: int
    active_word: str
    autocorrect_suggestions: List[str]
    last_committed_word: Optional[str] = None
    full_sentence: str
    inference_time_ms: float


class BinaryCodecStats(BaseModel):
    codec_name: str = "SignCodec-48B"
    bytes_per_frame: int = 48
    wire_rate_kbps_30fps: float = 1.152
    uncompressed_1080p_kbps: float = 1500.0
    bandwidth_reduction_pct: float = 99.23
    mpjpe_error_mm: float = 1.18
