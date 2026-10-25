"""
Root Application Entrypoint for Cloud Deployments (Render / Vercel / Railway / Docker)
Allows execution via `uvicorn app:app` or `uvicorn backend.sign0.main:app`.
"""

import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.sign0.main import app

__all__ = ["app"]
