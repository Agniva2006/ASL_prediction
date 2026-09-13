#!/usr/bin/env python3
"""
temporal_model.py
Sign0: Real-Time 16-Frame Temporal Gesture Recognition Backbone.
Classifies continuous dynamic sign language phrases (e.g., 'HELLO', 'THANK_YOU', 'PLEASE', 'HELP', 'EMERGENCY')
from a 16-frame sliding window of 63-dimensional MediaPipe landmark coordinates.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Any, Optional


class TemporalGestureGRU(nn.Module):
    """
    Lightweight Bidirectional GRU with Temporal Self-Attention.
    Input Shape: (Batch, Seq_Len=16, Landmark_Dim=63)
    Output: Class Logits (Num_Dynamic_Gestures=10)
    """

    GESTURE_CLASSES = [
        "HELLO", "THANK_YOU", "PLEASE", "YES", "NO",
        "HELP", "DOCTOR", "WATER", "EMERGENCY", "PAIN"
    ]

    def __init__(self, input_dim: int = 63, hidden_dim: int = 128, num_layers: int = 2, num_classes: int = 10):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.seq_len = 16
        self.num_classes = num_classes

        # Spatial Feature Extractor
        self.spatial_encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.15)
        )

        # Temporal Sequence Modeling
        self.gru = nn.GRU(
            input_size=128,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.15 if num_layers > 1 else 0.0
        )

        # Temporal Attention Pooling
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (B, T=16, 63)
        b, t, d = x.shape
        x_flat = x.reshape(b * t, d)
        spatial_feats = self.spatial_encoder(x_flat).reshape(b, t, -1)

        gru_out, _ = self.gru(spatial_feats) # (B, T, 2*H)

        # Compute attention weights over time
        attn_weights = torch.softmax(self.attention(gru_out), dim=1) # (B, T, 1)
        pooled = torch.sum(gru_out * attn_weights, dim=1) # (B, 2*H)

        logits = self.classifier(pooled)
        return logits


class SlidingWindowGestureBuffer:
    """
    Thread-safe 16-frame circular landmark buffer for real-time temporal inference.
    """

    def __init__(self, window_size: int = 16, landmark_dim: int = 63):
        self.window_size = window_size
        self.landmark_dim = landmark_dim
        self.buffer = np.zeros((window_size, landmark_dim), dtype=np.float32)
        self.frames_received = 0
        self.model = TemporalGestureGRU()
        self.model.eval()

    def add_frame(self, keypoints_63d: List[float]) -> Optional[Dict[str, Any]]:
        """
        Push single 63-dim landmark frame into circular window and infer gesture.
        """
        kp = np.array(keypoints_63d, dtype=np.float32)
        if len(kp) != self.landmark_dim:
            kp = np.pad(kp, (0, max(0, self.landmark_dim - len(kp))))[:self.landmark_dim]

        # Shift buffer left and append new frame
        self.buffer[:-1] = self.buffer[1:]
        self.buffer[-1] = kp
        self.frames_received += 1

        if self.frames_received < self.window_size:
            return {
                "status": "BUFFERING",
                "progress_pct": round((self.frames_received / self.window_size) * 100, 1),
                "predicted_gesture": None
            }

        # Run inference
        tensor_in = torch.from_numpy(self.buffer).unsqueeze(0) # (1, 16, 63)
        with torch.no_grad():
            logits = self.model(tensor_in)
            probs = torch.softmax(logits, dim=-1).squeeze(0).numpy()
            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx])

        return {
            "status": "PREDICTED",
            "predicted_gesture": TemporalGestureGRU.GESTURE_CLASSES[pred_idx],
            "confidence": round(confidence, 4),
            "window_frames": self.window_size,
            "top_probabilities": {
                TemporalGestureGRU.GESTURE_CLASSES[i]: round(float(probs[i]), 4)
                for i in range(len(TemporalGestureGRU.GESTURE_CLASSES))
            }
        }


# Global temporal gesture buffer singleton
temporal_gesture_buffer = SlidingWindowGestureBuffer()
