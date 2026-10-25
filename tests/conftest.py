"""
Pytest configuration and shared fixtures for Sign0 test suite.
"""

import sys
import os
import pytest
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.sign0.main import app


@pytest.fixture(scope="session")
def test_client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_landmarks_63():
    """63-dimensional normalized landmark array representing a realistic kinematic hand pose."""
    np.random.seed(42)
    wrist = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    pose = [wrist]
    flexion = [0.2, 0.3, 0.4, 0.5, 0.3]
    spread = [-0.15, -0.05, 0.0, 0.08, 0.15]
    for f in range(5):
        angle = spread[f]
        r = 0.04
        for j in range(4):
            joint = np.array([
                np.sin(angle) * r * (j + 1),
                np.cos(angle) * r * (j + 1) * (1.0 - flexion[f] * 0.4),
                -flexion[f] * 0.03 * (j + 1)
            ], dtype=np.float32)
            pose.append(joint)
    return np.array(pose, dtype=np.float32).flatten().tolist()


@pytest.fixture
def sample_sequence_16x63(sample_landmarks_63):
    """16 consecutive frames of 63-dimensional landmark coordinates."""
    seq = []
    base = np.array(sample_landmarks_63, dtype=np.float32)
    for t in range(16):
        jitter = np.sin(t * 0.2) * 0.005
        seq.append((base + jitter).tolist())
    return seq
