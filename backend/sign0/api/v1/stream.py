"""
Sign0 Real-Time Streaming & Neural Codec API Router (v1)
Endpoints:
- WebSocket /stream/ws: Continuous landmark stream with debouncing and word assembly
- WebSocket /stream/binary: 48-byte Neural Latent Codec binary stream
- GET /stream/codec/stats: Latency, bandwidth, and MPJPE metrics
"""

import json
import time
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from backend.sign0.services.inference_service import inference_engine
from backend.sign0.services.stream_processor import GestureStreamProcessor
from backend.sign0.services.sign_codec import sign_codec
from backend.sign0.schemas.stream import BinaryCodecStats
from backend.sign0.core.metrics import metrics
from backend.sign0.core.logging import logger

router = APIRouter(prefix="/stream", tags=["Real-Time Streaming & Codec"])


@router.websocket("/ws")
async def websocket_continuous_stream(websocket: WebSocket):
    """
    Real-Time WebSocket stream for browser webcam tracking.
    - Receives frame JSON containing 63 landmarks
    - Applies hold-duration debouncing (filters transition frames)
    - Surrounds active word with live predictive suggestions
    - Auto-spaces and commits full sentences on gesture pause
    """
    await websocket.accept()
    metrics.increment_ws()
    stream_processor = GestureStreamProcessor()
    logger.info("Client connected to continuous WebSocket stream")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            landmarks = payload.get("landmarks")
            if not landmarks or len(landmarks) != 63:
                await websocket.send_json({"error": "Expected 63 landmark coordinates"})
                continue

            # Run ultra-fast inference
            mlp_res = inference_engine.predict_mlp(landmarks)
            pred_letter = mlp_res["prediction"]
            confidence = mlp_res["confidence"]

            # Process through debouncing state machine
            stream_state = stream_processor.process_frame(pred_letter, confidence)
            stream_state["inference_time_ms"] = mlp_res["inference_time_ms"]

            await websocket.send_json(stream_state)

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket stream")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        metrics.decrement_ws()


@router.websocket("/binary")
async def websocket_binary_codec_stream(websocket: WebSocket):
    """
    Zero-Copy 48-byte Neural Latent Codec streaming channel.
    Accepts raw binary structs (12 float32s = 48 bytes) at 30 FPS (1.15 kbps wire rate).
    """
    await websocket.accept()
    metrics.increment_ws()
    stream_processor = GestureStreamProcessor()
    logger.info("Client connected to 48-byte binary codec stream")

    try:
        while True:
            data = await websocket.receive_bytes()
            if len(data) != 48:
                await websocket.send_json({"error": f"Expected 48-byte binary frame, got {len(data)}"})
                continue

            # Decompress latent vector into 63 continuous coordinates
            decoded = sign_codec.decode(data)
            landmarks = decoded["keypoints"]

            # Run inference on decompressed skeleton
            mlp_res = inference_engine.predict_mlp(landmarks)
            stream_state = stream_processor.process_frame(mlp_res["prediction"], mlp_res["confidence"])
            stream_state["keypoints"] = landmarks
            stream_state["wire_payload_bytes"] = 48

            await websocket.send_json(stream_state)

    except WebSocketDisconnect:
        logger.info("Client disconnected from binary codec stream")
    except Exception as e:
        logger.error(f"Binary stream error: {e}")
    finally:
        metrics.decrement_ws()


@router.get("/codec/stats", response_model=BinaryCodecStats)
def get_codec_specifications():
    """Returns technical compression, throughput, and error metrics for SignCodec."""
    return BinaryCodecStats()
