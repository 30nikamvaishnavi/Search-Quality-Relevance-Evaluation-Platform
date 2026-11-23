"""Unit tests for source credibility assessment."""

from __future__ import annotations

from src.evaluator.credibility import assess_source_credibility


def test_gov_edu_not_automatically_trusted_without_metadata() -> None:
    """A .gov or .edu domain without author, date, HTTPS, or references should not score artificially high."""
    gov_sparse = assess_source_credibility(
        url="http://legacy-agency.example.gov/old-notice",
        source_name="Unknown",
        author="",
        published_date="",
        supporting_evidence="",
    )
    org_transparent = assess_source_credibility(
        url="https://ir-engineering.example.org/hybrid-search",
        source_name="IR Engineering",
        author="K. Chen",
        published_date="2026-03-14",
        supporting_evidence="Includes reciprocal rank fusion benchmark citations.",
        reference_urls=["https://ir-engineering.example.org/papers/rrf"],
    )
    assert gov_sparse.automated_credibility_score < org_transparent.automated_credibility_score
    assert any(".gov" in c for c in gov_sparse.cautions)


def test_manual_credibility_adjustment_clamped() -> None:
    """Manual credibility adjustments modify final score while keeping automated score intact."""
    res = assess_source_credibility(
        url="https://example.org/article",
        source_name="Example Org",
        author="Jane Doe",
        published_date="2025-11-01",
        manual_adjustment=-20.0,
        reviewer_explanation="Outdated methodology noted by reviewer.",
    )
    assert res.manual_adjustment == -20.0
    assert res.final_credibility_score == max(0.0, round(res.automated_credibility_score - 20.0, 2))
    assert res.reviewer_explanation == "Outdated methodology noted by reviewer."
