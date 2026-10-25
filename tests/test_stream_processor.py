"""
Unit tests for GestureStreamProcessor state machine.
Validates hysteresis debouncing, hold duration, auto-space, and sentence formation.
"""

from backend.sign0.services.stream_processor import GestureStreamProcessor


def test_hysteresis_debouncing():
    """Verify transient / jitter frames are not committed immediately."""
    processor = GestureStreamProcessor(min_hold_frames=4, min_confidence=0.80)

    # 1 transient frame of 'A'
    res = processor.process_frame("A", 0.85)
    assert not res["is_steady"]
    assert res["active_word"] == ""

    # Another transient frame of 'B'
    res = processor.process_frame("B", 0.85)
    assert not res["is_steady"]
    assert res["active_word"] == ""


def test_hold_duration_commit():
    """Verify letter commits only after sustained steady pose."""
    processor = GestureStreamProcessor(min_hold_frames=3, min_confidence=0.75)

    # Frame 1
    processor.process_frame("H", 0.90)
    # Frame 2
    processor.process_frame("H", 0.90)
    # Frame 3 -> Should commit 'H'
    res = processor.process_frame("H", 0.90)

    assert res["is_steady"]
    assert "H" in res["active_word"]


def test_space_and_word_assembly():
    """Verify 'space' sign triggers word commit and sentence assembly."""
    processor = GestureStreamProcessor(min_hold_frames=2, min_confidence=0.75)

    # Sign 'N', 'O'
    processor.process_frame("N", 0.90)
    processor.process_frame("N", 0.90)

    processor.process_frame("O", 0.90)
    processor.process_frame("O", 0.90)

    assert processor.active_word == "NO"

    # Space sign
    res = processor.process_frame("space", 0.90)
    assert "NO" in res["full_sentence"]
    assert processor.active_word == ""
