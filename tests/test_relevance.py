"""Unit tests for TF-IDF relevance and rule-based intent alignment."""

from __future__ import annotations

from src.evaluator.relevance import compute_tfidf_cosine, detect_query_intent, evaluate_relevance


def test_tfidf_cosine_boundaries() -> None:
    """Similarity scores must remain bounded within [0, 100]."""
    identical = compute_tfidf_cosine("python list comprehension", "python list comprehension")
    disjoint = compute_tfidf_cosine("quantum physics optics", "chocolate cake recipe")
    assert 95.0 <= identical <= 100.0
    assert disjoint == 0.0


def test_empty_query_handling() -> None:
    """Empty query returns zeroed scores with an informative warning."""
    res = evaluate_relevance(
        query="   ",
        title="Python Guide",
        description="A detailed tutorial on Python lists.",
    )
    assert res.overall_relevance_score == 0.0
    assert res.query_title_similarity == 0.0
    assert res.query_description_similarity == 0.0
    assert res.warnings


def test_missing_description_handling() -> None:
    """Missing description sets description similarity to 0 and adds a warning."""
    res = evaluate_relevance(
        query="python list comprehensions",
        title="Python List Comprehensions Guide",
        description="",
    )
    assert res.query_description_similarity == 0.0
    assert res.query_title_similarity > 50.0
    assert any("missing" in w.lower() for w in res.warnings)


def test_intent_detection_and_alignment() -> None:
    """Rule-based intent classifier detects informational, navigational, transactional, and timely queries."""
    assert detect_query_intent("how to learn python") == "informational"
    assert detect_query_intent("official fafsa application portal") == "navigational"
    assert detect_query_intent("compare best accounting software pricing") == "transactional"
    assert detect_query_intent("latest 2026 municipal microgrid news") == "timely"

    res = evaluate_relevance(
        query="how do python list comprehensions work",
        title="How Python List Comprehensions Work: Step-by-Step Guide",
        description=(
            "This guide explains how list comprehensions work in Python with examples, "
            "conditional filtering steps, and clear explanations for beginners."
        ),
        source_name="Python Learning Lab",
    )
    assert res.detected_intent == "informational"
    assert res.intent_alignment_score >= 70.0
    assert "lexical" in res.disclaimer.lower()
