"""
Unit tests for ONNX Runtime Inference Engine.
"""

from backend.sign0.services.inference_service import inference_engine


def test_mlp_inference(sample_landmarks_63):
    """Verify Static MLP inference returns predicted class, confidence, and latency."""
    res = inference_engine.predict_mlp(sample_landmarks_63)

    assert "prediction" in res
    assert isinstance(res["prediction"], str)
    assert 0.0 <= res["confidence"] <= 1.0
    assert "inference_time_ms" in res
    assert res["inference_time_ms"] >= 0.0


def test_quantized_int8_inference(sample_landmarks_63):
    """Verify INT8 quantized inference execution."""
    res = inference_engine.predict_mlp(sample_landmarks_63, use_int8=True)

    assert "prediction" in res
    assert "inference_time_ms" in res


def test_transformer_inference(sample_sequence_16x63):
    """Verify Spatial-Temporal Transformer inference on 16-frame sequence."""
    res = inference_engine.predict_transformer(sample_sequence_16x63)

    assert "gesture" in res
    assert res["frame_count"] == 16
    assert 0.0 <= res["confidence"] <= 1.0
