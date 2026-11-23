"""Unit tests for configurable weighted scoring and missing-evidence behavior."""

from __future__ import annotations

import pytest

from src.evaluator.scoring import DEFAULT_WEIGHTS, compute_overall_score, normalize_weights


def test_normalize_weights_sums_to_one() -> None:
    """Arbitrary positive weights normalize cleanly to 1.0."""
    norm = normalize_weights(
        {
            "search_relevance": 60,
            "content_quality": 40,
            "source_credibility": 40,
            "factual_evidence": 40,
            "intent_alignment": 20,
        }
    )
    assert pytest.approx(sum(norm.values()), abs=1e-5) == 1.0
    assert pytest.approx(norm["search_relevance"], abs=1e-5) == 0.30


def test_invalid_weights_raise_value_error() -> None:
    """Negative or all-zero weights are rejected."""
    with pytest.raises(ValueError):
        normalize_weights({k: 0.0 for k in DEFAULT_WEIGHTS})
    bad = dict(DEFAULT_WEIGHTS)
    bad["search_relevance"] = -0.1
    with pytest.raises(ValueError):
        normalize_weights(bad)


def test_missing_evidence_triggers_warning_and_zero_factual_contribution() -> None:
    """Without adequate factual evidence, warning is shown and factual component contributes 0."""
    res = compute_overall_score(
        search_relevance=90.0,
        content_quality=80.0,
        source_credibility=80.0,
        intent_alignment=80.0,
        factual_evidence=None,
        has_adequate_evidence=False,
    )
    assert res.has_adequate_evidence is False
    assert res.insufficient_evidence_warning is not None
    assert "unverified" in res.evidence_status.lower()
    expected = round(0.30 * 90 + 0.20 * 80 + 0.20 * 80 + 0.20 * 0 + 0.10 * 80, 2)
    assert res.automated_score == expected


def test_human_override_keeps_automated_score_separate() -> None:
    """Human reviewer overrides never erase the underlying automated score."""
    res = compute_overall_score(
        search_relevance=80.0,
        content_quality=80.0,
        source_credibility=80.0,
        intent_alignment=80.0,
        factual_evidence=90.0,
        has_adequate_evidence=True,
        human_label="Partially Relevant",
        human_score_override=55.0,
        human_comments="Snippet misses key technical constraint.",
    )
    assert res.automated_score == 82.0
    assert res.final_display_score == 55.0
    assert res.human_label == "Partially Relevant"
    assert res.score_source == "Human Reviewer Override"
