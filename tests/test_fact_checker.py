"""Unit tests for human-assisted fact verification and evidence guardrails."""

from __future__ import annotations

from src.evaluator.fact_checker import (
    ClaimStatus,
    summarize_fact_checks,
    validate_and_create_claim,
)


def test_cannot_mark_supported_without_evidence_and_url() -> None:
    """Guardrail prevents marking claims Supported or Contradicted without evidence and valid URLs."""
    claim, errors = validate_and_create_claim(
        claim_text="Water boils at 100C at sea level.",
        supporting_evidence="",
        source_urls=[],
        requested_status=ClaimStatus.SUPPORTED.value,
    )
    assert claim is None
    assert len(errors) >= 2


def test_unverified_claim_allowed_without_evidence() -> None:
    """Unverified status is permitted when evidence has not yet been gathered."""
    claim, errors = validate_and_create_claim(
        claim_text="Fiber moderates post-meal glucose spikes.",
        supporting_evidence="",
        source_urls=[],
        requested_status=ClaimStatus.UNVERIFIED.value,
    )
    assert claim is not None
    assert errors == []
    assert claim.status == ClaimStatus.UNVERIFIED.value


def test_fact_summary_counts_and_insufficient_evidence() -> None:
    """Summary tracks Supported, Contradicted, Unverified counts and missing-evidence warning."""
    empty_summary = summarize_fact_checks([])
    assert empty_summary["has_adequate_evidence"] is False
    assert empty_summary["factual_evidence_score"] is None
    assert "insufficient" in empty_summary["insufficient_evidence_warning"].lower()

    c1, _ = validate_and_create_claim(
        claim_text="TLS 1.3 reduces handshake round trips to 1-RTT.",
        supporting_evidence="Confirmed in synthetic protocol documentation section 2.",
        source_urls=["https://netsec.example.org/tls13"],
        requested_status=ClaimStatus.SUPPORTED.value,
    )
    c2, _ = validate_and_create_claim(
        claim_text="Herbal tea guarantees universal flu immunity.",
        supporting_evidence="Contradicted by synthetic clinical review document.",
        source_urls=["https://health.example.org/flu-review"],
        requested_status=ClaimStatus.CONTRADICTED.value,
    )
    assert c1 is not None and c2 is not None
    summary = summarize_fact_checks([c1, c2])
    assert summary["has_adequate_evidence"] is True
    assert summary["supported_count"] == 1
    assert summary["contradicted_count"] == 1
    assert summary["factual_evidence_score"] is not None
    assert summary["factual_evidence_score"] < 55.0
