"""Unit tests for content quality evaluation."""

from __future__ import annotations

from src.evaluator.content_quality import evaluate_content_quality


def test_high_quality_informative_content() -> None:
    """Substantive, readable content with metadata scores well."""
    res = evaluate_content_quality(
        query="seasonal influenza prevention guidelines",
        title="Seasonal Influenza Prevention Guidelines",
        description=(
            "This guide outlines 4 practical seasonal influenza prevention steps, including annual "
            "vaccination, regular handwashing with soap, staying home when symptomatic, and improving indoor ventilation."
        ),
        source_name="Synthetic Public Health Reference",
        published_date="2025-10-05",
        supporting_evidence="Summarizes clinical guidance on annual vaccination and hygiene.",
    )
    assert res.overall_quality_score >= 70.0
    assert res.completeness_score >= 80.0
    assert res.word_count >= 20


def test_missing_description_quality_penalty() -> None:
    """Missing description produces zero readability/uniqueness and emits warnings."""
    res = evaluate_content_quality(
        query="python tutorial",
        title="Python Tutorial",
        description="",
    )
    assert res.word_count == 0
    assert res.readability_score == 0.0
    assert res.uniqueness_score == 0.0
    assert len(res.warnings) >= 1


def test_clickbait_and_repetition_penalties() -> None:
    """Clickbait phrases and repeated sentences reduce usefulness and uniqueness."""
    res = evaluate_content_quality(
        query="flu prevention",
        title="Flu Prevention",
        description=(
            "Miracle cure! Doctors hate this secret trick. Miracle cure! Doctors hate this secret trick."
        ),
    )
    assert res.usefulness_score < 50.0
    assert res.uniqueness_score < 85.0
    assert any("clickbait" in w.lower() or "repetitive" in w.lower() for w in res.warnings)
