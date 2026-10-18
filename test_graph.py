"""Small offline tests for deterministic agent fallback logic."""
from agent import _fallback_answer


def test_fallback_mentions_revision_topic():
    context = {
        "learning_events": [
            {"topic": "Normalization", "result": "needs_revision", "score": 40}
        ],
        "prerequisites": [
            {"prerequisite": "Relational Model", "next_topic": "Normalization"}
        ],
    }
    answer = _fallback_answer("What should I revise next?", context)
    assert "Normalization" in answer
    assert "Relational Model" in answer


def test_fallback_does_not_claim_low_score_without_evidence():
    context = {"learning_events": [], "prerequisites": []}
    answer = _fallback_answer("What should I study next?", context)
    assert "don't see a low-score" in answer
