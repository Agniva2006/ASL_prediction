"""
Unit tests for Sign0 Vocabulary & Autocorrect Spell Engine.
"""

from backend.sign0.services.spell_engine import spell_engine


def test_trie_prefix_matching():
    """Verify predictive typing completions for fingerspelling prefixes."""
    completions = spell_engine.get_prefix_completions("HEL", max_results=3)
    assert len(completions) > 0
    assert "HELLO" in completions or "HELP" in completions


def test_emergency_vocabulary_present():
    """Verify high-priority clinical and emergency terms exist in vocabulary."""
    emergency_terms = ["HELP", "EMERGENCY", "DOCTOR", "PAIN", "WATER", "HOSPITAL"]
    for term in emergency_terms:
        assert term in spell_engine.words, f"Missing critical term: {term}"


def test_fuzzy_autocorrect():
    """Verify typo correction using Levenshtein distance."""
    # Test common fingerspelling typos
    suggestions = spell_engine.suggest_corrections("HLLP", max_distance=1)
    assert "HELP" in suggestions

    doctor_suggestions = spell_engine.suggest_corrections("DOCTR", max_distance=1)
    assert "DOCTOR" in doctor_suggestions
