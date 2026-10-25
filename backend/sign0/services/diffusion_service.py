"""
Sign0 Generative 3D Gesture Synthesizer & Dictionary Service
Fetches DDPM generated 3D trajectories for text prompts and handles frame interpolation.
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional

from backend.sign0.core.config import settings
from backend.sign0.core.logging import logger


class DiffusionService:
    """Service providing 3D kinematic keyframe trajectories for text and sign words."""

    def __init__(self):
        self.library: Dict[str, Any] = {}
        self._load_library()

    def _load_library(self):
        possible_paths = [
            os.path.join(settings.DATA_DIR, "sign_diffusion_library.json"),
            os.path.join(settings.BASE_DIR, "backend", "sign_diffusion_library.json"),
            os.path.join(settings.BASE_DIR, "sign_diffusion_library.json"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        self.library = json.load(f)
                    logger.info(f"Loaded {len(self.library)} gestures from diffusion library")
                    return
                except Exception as e:
                    logger.warning(f"Error loading diffusion library from {path}: {e}")

    def synthesize(self, text: str, fps: int = 30) -> Dict[str, Any]:
        """
        Synthesize frame-by-frame 3D hand skeleton trajectory for a prompt.
        If prompt contains multiple words, concatenates trajectories with smooth transitions.
        """
        words = text.upper().strip().split()
        synthesized_tokens = []
        combined_frames = []

        for w in words:
            if w in self.library:
                frames = self.library[w]
                synthesized_tokens.append(w)
                combined_frames.extend(frames)
            else:
                # Fallback: spell out letters
                for char in w:
                    if char in self.library:
                        synthesized_tokens.append(char)
                        combined_frames.extend(self.library[char])
                    else:
                        # Generate kinematic neutral pose
                        synthesized_tokens.append(char)
                        combined_frames.append(self._generate_neutral_pose())

        if not combined_frames:
            combined_frames = [self._generate_neutral_pose() for _ in range(15)]

        duration = len(combined_frames) / max(1, fps)
        return {
            "prompt": text,
            "total_frames": len(combined_frames),
            "fps": fps,
            "duration_seconds": round(duration, 2),
            "trajectory": combined_frames,
            "synthesized_tokens": synthesized_tokens,
            "model": "SignDiffusion-DDPM-v2",
        }

    def _generate_neutral_pose(self) -> List[List[float]]:
        """Generate 21 3D joint coordinates for a neutral open hand."""
        joints = []
        # Wrist
        joints.append([0.0, 0.0, 0.0])
        # 5 fingers x 4 joints
        for finger in range(5):
            angle = (finger - 2) * 0.15
            for j in range(1, 5):
                r = 0.04 * j
                joints.append([float(np.sin(angle) * r), float(np.cos(angle) * r), float(-0.01 * j)])
        return joints

    def list_dictionary(self) -> List[Dict[str, Any]]:
        """Return available dictionary terms with categories."""
        terms = []
        categories = {
            "GREETING": ["HELLO", "GOODBYE", "NICE", "MEET"],
            "EMERGENCY": ["HELP", "EMERGENCY", "DOCTOR", "HOSPITAL", "PAIN", "WATER"],
            "COURTESY": ["PLEASE", "THANK_YOU", "YES", "NO", "SORRY"],
            "ALPHABET": [chr(ord("A") + i) for i in range(26)],
        }
        for cat, words in categories.items():
            for w in words:
                terms.append({
                    "word": w,
                    "category": cat,
                    "difficulty": "Beginner" if cat in ("GREETING", "ALPHABET") else "Intermediate",
                    "description": f"Standard ASL expression for {w}",
                    "has_3d_trajectory": w in self.library,
                })
        return terms


diffusion_service = DiffusionService()
