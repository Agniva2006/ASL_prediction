"""Pydantic 3D Gesture Synthesis & Dictionary Schemas."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    fps: int = Field(default=30, ge=15, le=60)
    smooth_transitions: bool = True


class Keyframe3D(BaseModel):
    frame_index: int
    joints: List[List[float]]  # 21 joints x [x, y, z]


class SynthesisResponse(BaseModel):
    prompt: str
    total_frames: int
    fps: int
    duration_seconds: float
    trajectory: List[List[List[float]]]  # [frames, 21_joints, 3_coords]
    synthesized_tokens: List[str]
    model: str = "SignDiffusion-DDPM-v2"


class DictionaryItem(BaseModel):
    word: str
    category: str
    difficulty: str
    description: str
    has_3d_trajectory: bool
