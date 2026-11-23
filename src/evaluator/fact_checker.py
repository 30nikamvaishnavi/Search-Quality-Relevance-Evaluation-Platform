"""Human-assisted factual accuracy review and evidence tracking module."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import numpy as np

from src.utils.validators import sanitize_text, validate_url


class ClaimStatus(StrEnum):
    """Allowed verification statuses for factual claims."""

    SUPPORTED = "Supported"
    CONTRADICTED = "Contradicted"
    UNVERIFIED = "Unverified"


VALID_CLAIM_STATUSES = {status.value for status in ClaimStatus}


@dataclass
class FactClaim:
    """Represents a human-reviewed factual claim with supporting evidence."""

    claim_id: str
    claim_text: str
    supporting_evidence: str = ""
    source_urls: list[str] = field(default_factory=list)
    status: str = ClaimStatus.UNVERIFIED.value
    reviewer_notes: str = ""
    result_title: str = ""
    reviewed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize claim to dictionary."""
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "supporting_evidence": self.supporting_evidence,
            "source_urls": self.source_urls,
            "status": self.status,
            "reviewer_notes": self.reviewer_notes,
            "result_title": self.result_title,
            "reviewed_at": self.reviewed_at,
        }


def validate_and_create_claim(
    claim_text: str,
    supporting_evidence: str = "",
    source_urls: list[str] | None = None,
    requested_status: str = ClaimStatus.UNVERIFIED.value,
    reviewer_notes: str = "",
    result_title: str = "",
    claim_id: str | None = None,
) -> tuple[FactClaim | None, list[str]]:
    """Validate a factual claim and enforce evidence requirements.

    A claim cannot be marked Supported or Contradicted without both
    supporting evidence text and at least one valid http/https source URL.
    """
    errors: list[str] = []
    clean_claim = sanitize_text(claim_text)
    clean_evidence = sanitize_text(supporting_evidence)
    clean_notes = sanitize_text(reviewer_notes)
    clean_result_title = sanitize_text(result_title)
    raw_urls = [sanitize_text(u) for u in (source_urls or []) if sanitize_text(u)]

    if not clean_claim or len(clean_claim) < 5:
        errors.append("Factual claim must be at least 5 characters long.")

    if requested_status not in VALID_CLAIM_STATUSES:
        errors.append(f"Invalid claim status '{requested_status}'. Choose Supported, Contradicted, or Unverified.")

    valid_urls: list[str] = []
    for url in raw_urls:
        ok, msg = validate_url(url)
        if not ok:
            errors.append(f"Invalid evidence URL '{url}': {msg}")
        else:
            valid_urls.append(url)

    # Guardrail: never allow Supported or Contradicted without adequate evidence
    if requested_status in {ClaimStatus.SUPPORTED.value, ClaimStatus.CONTRADICTED.value}:
        if len(clean_evidence) < 10:
            errors.append(
                f"Cannot mark claim as '{requested_status}' without adequate supporting evidence (minimum 10 characters)."
            )
        if not valid_urls:
            errors.append(
                f"Cannot mark claim as '{requested_status}' without at least one valid source URL."
            )

    if errors:
        return None, errors

    claim = FactClaim(
        claim_id=claim_id or f"claim-{uuid.uuid4().hex[:8]}",
        claim_text=clean_claim,
        supporting_evidence=clean_evidence,
        source_urls=valid_urls,
        status=requested_status,
        reviewer_notes=clean_notes,
        result_title=clean_result_title,
        reviewed_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    return claim, []


def summarize_fact_checks(claims: list[dict[str, Any] | FactClaim]) -> dict[str, Any]:
    """Summarize human-reviewed claims and compute an evidence-backed assessment score."""
    normalized: list[dict[str, Any]] = [
        c.to_dict() if isinstance(c, FactClaim) else c for c in claims
    ]

    total = len(normalized)
    supported = 0
    contradicted = 0
    unverified = 0
    evidence_backed_verified = 0

    for item in normalized:
        status = item.get("status", ClaimStatus.UNVERIFIED.value)
        evidence = sanitize_text(item.get("supporting_evidence"))
        urls = [u for u in item.get("source_urls", []) if validate_url(u)[0]]
        has_evidence = len(evidence) >= 10 and len(urls) > 0

        if status == ClaimStatus.SUPPORTED.value and has_evidence:
            supported += 1
            evidence_backed_verified += 1
        elif status == ClaimStatus.CONTRADICTED.value and has_evidence:
            contradicted += 1
            evidence_backed_verified += 1
        else:
            unverified += 1

    if total == 0 or evidence_backed_verified == 0:
        return {
            "total_claims": total,
            "supported_count": supported,
            "contradicted_count": contradicted,
            "unverified_count": unverified,
            "has_adequate_evidence": False,
            "factual_evidence_score": None,
            "insufficient_evidence_warning": (
                "Insufficient factual evidence provided. Accuracy has NOT been verified."
            ),
        }

    # Score reflects reviewer-verified evidence ratio; contradicted claims sharply penalize
    raw_score = ((supported * 100.0) + (unverified * 35.0) + (contradicted * 0.0)) / total
    if contradicted > 0:
        raw_score = min(raw_score, max(0.0, 55.0 - contradicted * 15.0))

    score = round(float(np.clip(raw_score, 0.0, 100.0)), 2)

    warning: str | None = None
    if unverified > 0:
        warning = (
            f"{unverified} of {total} claim(s) remain Unverified due to incomplete evidence."
        )

    return {
        "total_claims": total,
        "supported_count": supported,
        "contradicted_count": contradicted,
        "unverified_count": unverified,
        "has_adequate_evidence": True,
        "factual_evidence_score": score,
        "insufficient_evidence_warning": warning,
    }
