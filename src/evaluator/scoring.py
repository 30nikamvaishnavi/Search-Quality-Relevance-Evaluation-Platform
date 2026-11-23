"""Configurable weighted scoring engine separating automated heuristics from human judgment."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.utils.validators import sanitize_text, validate_score

DEFAULT_WEIGHTS: dict[str, float] = {
    "search_relevance": 0.30,
    "content_quality": 0.20,
    "source_credibility": 0.20,
    "factual_evidence": 0.20,
    "intent_alignment": 0.10,
}

RELEVANCE_LABELS = ("Relevant", "Partially Relevant", "Irrelevant")


@dataclass
class OverallScoreResult:
    """Overall evaluation score breaking down automated signals and human reviewer judgment."""

    automated_score: float
    normalized_weights: dict[str, float]
    component_scores: dict[str, float | None]
    has_adequate_evidence: bool
    evidence_status: str
    insufficient_evidence_warning: str | None
    human_label: str | None = None
    human_score_override: float | None = None
    human_comments: str = ""
    final_display_score: float = 0.0
    score_source: str = "Automated Heuristic"
    band: str = "Needs Review"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize overall scoring result to a dictionary."""
        return {
            "automated_score": self.automated_score,
            "normalized_weights": self.normalized_weights,
            "component_scores": self.component_scores,
            "has_adequate_evidence": self.has_adequate_evidence,
            "evidence_status": self.evidence_status,
            "insufficient_evidence_warning": self.insufficient_evidence_warning,
            "human_label": self.human_label,
            "human_score_override": self.human_score_override,
            "human_comments": self.human_comments,
            "final_display_score": self.final_display_score,
            "score_source": self.score_source,
            "band": self.band,
            "notes": self.notes,
        }


def normalize_weights(weights: dict[str, float] | None = None) -> dict[str, float]:
    """Validate and normalize component weights so they sum to 1.0."""
    source = dict(DEFAULT_WEIGHTS if weights is None else weights)
    expected_keys = set(DEFAULT_WEIGHTS.keys())
    if set(source.keys()) != expected_keys:
        missing = sorted(expected_keys - set(source.keys()))
        extra = sorted(set(source.keys()) - expected_keys)
        raise ValueError(f"Weight keys mismatch. Missing: {missing}, unexpected: {extra}.")

    cleaned: dict[str, float] = {}
    for key, val in source.items():
        if isinstance(val, bool) or val is None:
            raise ValueError(f"Weight for '{key}' must be numeric.")
        num = float(val)
        if math.isnan(num) or math.isinf(num) or num < 0.0:
            raise ValueError(f"Weight for '{key}' must be a finite non-negative number.")
        cleaned[key] = num

    total = sum(cleaned.values())
    if total <= 0.0:
        raise ValueError("Total weight across scoring components must be greater than 0.")

    return {key: round(val / total, 6) for key, val in cleaned.items()}


def classify_score_band(score: float, has_adequate_evidence: bool) -> str:
    """Assign a human-readable quality band based on score and evidence availability."""
    if not has_adequate_evidence:
        if score >= 65.0:
            return "Promising Match (Accuracy Unverified)"
        if score >= 40.0:
            return "Moderate Match (Accuracy Unverified)"
        return "Low Quality / Unverified"
    if score >= 80.0:
        return "High Quality"
    if score >= 60.0:
        return "Moderate Quality"
    if score >= 40.0:
        return "Borderline Quality"
    return "Low Quality"


def compute_overall_score(
    search_relevance: float,
    content_quality: float,
    source_credibility: float,
    intent_alignment: float,
    factual_evidence: float | None = None,
    has_adequate_evidence: bool = False,
    weights: dict[str, float] | None = None,
    human_label: str | None = None,
    human_score_override: float | None = None,
    human_comments: str = "",
) -> OverallScoreResult:
    """Compute configurable weighted score and keep human judgment clearly separated."""
    norm_weights = normalize_weights(weights)

    for name, val in (
        ("search_relevance", search_relevance),
        ("content_quality", content_quality),
        ("source_credibility", source_credibility),
        ("intent_alignment", intent_alignment),
    ):
        ok, msg = validate_score(val)
        if not ok:
            raise ValueError(f"Invalid '{name}' score: {msg}")

    if factual_evidence is not None:
        ok, msg = validate_score(factual_evidence)
        if not ok:
            raise ValueError(f"Invalid 'factual_evidence' score: {msg}")

    notes: list[str] = []
    if has_adequate_evidence and factual_evidence is not None:
        effective_factual = float(factual_evidence)
        evidence_status = "Evidence Reviewed"
        warning = None
    else:
        # Missing evidence contributes 0 so unverified results cannot achieve inflated scores
        effective_factual = 0.0
        evidence_status = "Insufficient Evidence — Accuracy Unverified"
        warning = (
            "Insufficient factual evidence provided. Factual accuracy has NOT been verified, "
            "so the factual evidence component contributes 0 to the automated weighted score."
        )
        notes.append(warning)

    automated_raw = (
        norm_weights["search_relevance"] * float(search_relevance)
        + norm_weights["content_quality"] * float(content_quality)
        + norm_weights["source_credibility"] * float(source_credibility)
        + norm_weights["factual_evidence"] * effective_factual
        + norm_weights["intent_alignment"] * float(intent_alignment)
    )
    automated_score = round(float(np.clip(automated_raw, 0.0, 100.0)), 2)

    cleaned_label = sanitize_text(human_label) if human_label else None
    if cleaned_label and cleaned_label not in RELEVANCE_LABELS:
        raise ValueError(f"Invalid human_label '{cleaned_label}'. Must be one of {RELEVANCE_LABELS}.")

    cleaned_override: float | None = None
    if human_score_override is not None:
        ok, msg = validate_score(human_score_override)
        if not ok:
            raise ValueError(f"Invalid human_score_override: {msg}")
        cleaned_override = round(float(human_score_override), 2)

    cleaned_comments = sanitize_text(human_comments)

    if cleaned_override is not None:
        final_display = cleaned_override
        score_source = "Human Reviewer Override"
        notes.append(
            f"Final score reflects manual reviewer override ({cleaned_override}/100) rather than automated score ({automated_score}/100)."
        )
    else:
        final_display = automated_score
        score_source = "Automated Heuristic"

    band = classify_score_band(final_display, has_adequate_evidence)

    return OverallScoreResult(
        automated_score=automated_score,
        normalized_weights=norm_weights,
        component_scores={
            "search_relevance": round(float(search_relevance), 2),
            "content_quality": round(float(content_quality), 2),
            "source_credibility": round(float(source_credibility), 2),
            "factual_evidence": round(float(factual_evidence), 2) if factual_evidence is not None else None,
            "intent_alignment": round(float(intent_alignment), 2),
        },
        has_adequate_evidence=has_adequate_evidence,
        evidence_status=evidence_status,
        insufficient_evidence_warning=warning,
        human_label=cleaned_label,
        human_score_override=cleaned_override,
        human_comments=cleaned_comments,
        final_display_score=final_display,
        score_source=score_source,
        band=band,
        notes=notes,
    )
