"""
Sign0 3D Gesture Synthesis & Dictionary API Router (v1)
Endpoints:
- POST /synthesis/generate: Synthesize 3D kinematic keyframe trajectories from text
- GET /synthesis/dictionary: Interactive dictionary index with 3D trajectories
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from backend.sign0.schemas.synthesis import SynthesisRequest, SynthesisResponse, DictionaryItem
from backend.sign0.services.diffusion_service import diffusion_service

router = APIRouter(prefix="/synthesis", tags=["Generative 3D Synthesis"])


@router.post("/generate", response_model=SynthesisResponse)
@router.post("/diffuse", response_model=SynthesisResponse)
def synthesize_gesture_from_text(req: SynthesisRequest):
    """
    Synthesize frame-by-frame 3D hand skeleton kinematic trajectories from input text.
    Uses DDPM generative sign models with smooth bone rotation matrices.
    """
    res = diffusion_service.synthesize(text=req.text, fps=req.fps)
    return res


@router.get("/dictionary", response_model=List[DictionaryItem])
def get_dictionary_terms():
    """Retrieve full catalog of sign language dictionary words with categories and trajectory availability."""
    return diffusion_service.list_dictionary()
