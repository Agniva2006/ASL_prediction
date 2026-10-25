"""
Sign0 Real-Time Gesture Stream Processor & Sentence Assembler
Implements hold-duration hysteresis debouncing, auto-space detection, and vocabulary spell integration.
"""

import time
from typing import Dict, Any, List, Optional
from backend.sign0.services.spell_engine import spell_engine
from backend.sign0.core.metrics import metrics


class GestureStreamProcessor:
    """
    Production-grade stream processing state machine.
    Transforms noisy frame-by-frame letter predictions into clean words and sentences.
    - Hysteresis Debouncing: Filters transition frames between signs.
    - Hold-Time Filter: Requires steady pose for minimum N frames before registration.
    - Auto-Spacing: Detects natural pauses (> 800ms) to commit word tokens.
    - Live Autocorrect: Continuously surfaces dictionary completions.
    """

    def __init__(
        self,
        min_hold_frames: int = 5,
        min_confidence: float = 0.70,
        pause_threshold_sec: float = 0.90,
    ):
        self.min_hold_frames = min_hold_frames
        self.min_confidence = min_confidence
        self.pause_threshold_sec = pause_threshold_sec

        # State Variables
        self.current_candidate: Optional[str] = None
        self.candidate_streak: int = 0
        self.last_committed_letter: Optional[str] = None
        self.last_frame_time: float = time.time()
        self.last_steady_time: float = time.time()

        self.active_word: str = ""
        self.committed_words: List[str] = []

    def process_frame(self, predicted_letter: str, confidence: float) -> Dict[str, Any]:
        """
        Process a single video frame prediction.
        Returns the instantaneous stream state, word tokens, and sentence progression.
        """
        now = time.time()
        time_since_last_steady = now - self.last_steady_time

        # Check for pause / word completion
        if self.active_word and time_since_last_steady > self.pause_threshold_sec:
            self._commit_active_word()

        is_steady = False

        if confidence >= self.min_confidence and predicted_letter not in ("nothing", "del", "space", "unknown"):
            if predicted_letter == self.current_candidate:
                self.candidate_streak += 1
            else:
                self.current_candidate = predicted_letter
                self.candidate_streak = 1

            # Check if hold duration met
            if self.candidate_streak >= self.min_hold_frames:
                is_steady = True
                self.last_steady_time = now

                # Avoid duplicate registration of the same held letter
                if predicted_letter != self.last_committed_letter:
                    self.active_word += predicted_letter
                    self.last_committed_letter = predicted_letter
        elif predicted_letter == "space" and confidence >= self.min_confidence:
            if self.active_word:
                self._commit_active_word()
            self.last_committed_letter = "space"
        elif predicted_letter == "del" and confidence >= self.min_confidence:
            if self.active_word:
                self.active_word = self.active_word[:-1]
            self.last_committed_letter = "del"
        else:
            # Low confidence or transition frame
            self.candidate_streak = 0
            self.current_candidate = None
            self.last_committed_letter = None

        self.last_frame_time = now

        # Get real-time predictive suggestions
        suggestions = (
            spell_engine.get_prefix_completions(self.active_word, max_results=3)
            if self.active_word
            else []
        )

        full_sentence = " ".join(self.committed_words)
        if self.active_word:
            full_sentence = f"{full_sentence} {self.active_word}".strip()

        return {
            "predicted_letter": predicted_letter,
            "confidence": round(confidence, 4),
            "is_steady": is_steady,
            "hold_frames": self.candidate_streak,
            "active_word": self.active_word,
            "autocorrect_suggestions": suggestions,
            "last_committed_word": self.committed_words[-1] if self.committed_words else None,
            "full_sentence": full_sentence,
        }

    def _commit_active_word(self):
        """Autocorrect and commit the active word to the final sentence."""
        raw_word = self.active_word.strip()
        if not raw_word:
            return

        # Check if correction needed
        corrections = spell_engine.suggest_corrections(raw_word, max_distance=1, max_results=1)
        final_word = corrections[0] if corrections else raw_word

        self.committed_words.append(final_word)
        self.active_word = ""
        self.last_committed_letter = None
        metrics.record_word_assembled()

    def reset(self):
        """Clear the current stream accumulator."""
        self.current_candidate = None
        self.candidate_streak = 0
        self.last_committed_letter = None
        self.active_word = ""
        self.committed_words = []
