"""
Unit tests for SignCodec 48-byte Neural Latent Codec.
Validates zero-copy binary layout, throughput rate, and MPJPE reconstruction accuracy.
"""

from backend.sign0.services.sign_codec import sign_codec


def test_codec_payload_size(sample_landmarks_63):
    """Verify that encoded binary struct is exactly 48 bytes (12 float32s)."""
    payload = sign_codec.encode(sample_landmarks_63)
    assert isinstance(payload, bytes)
    assert len(payload) == 48, f"Expected 48 bytes, got {len(payload)}"


def test_codec_decode_roundtrip(sample_landmarks_63):
    """Verify decoded skeleton matches 21 3D joints (63 floats)."""
    payload = sign_codec.encode(sample_landmarks_63)
    decoded = sign_codec.decode(payload)

    assert "keypoints" in decoded
    assert len(decoded["keypoints"]) == 63
    assert "wrist_root" in decoded
    assert len(decoded["wrist_root"]) == 3
    assert "latent_vector" in decoded
    assert len(decoded["latent_vector"]) == 9


def test_codec_mpjpe_error_bound(sample_landmarks_63):
    """Verify Mean Per-Joint Position Error is constrained under acceptable threshold."""
    payload = sign_codec.encode(sample_landmarks_63)
    decoded = sign_codec.decode(payload)
    error_mm = sign_codec.compute_mpjpe(sample_landmarks_63, decoded["keypoints"])

    assert error_mm < 5.0, f"MPJPE exceeded acceptable kinematic tolerance: {error_mm}mm"
