"""Transparent source credibility assessment with manual reviewer adjustments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import numpy as np

from src.utils.validators import sanitize_text, validate_date_string, validate_url

DOMAIN_CATEGORIES = {
    ".gov": "Government / Public Sector Domain",
    ".edu": "Educational / Academic Domain",
    ".org": "Non-Profit / Organization Domain",
    ".ac": "Academic Institution Domain",
    ".com": "Commercial Domain",
    ".net": "Network / General Domain",
    ".invalid": "Synthetic / Demonstration Domain",
}

GENERIC_SOURCE_NAMES = {"unknown", "website", "blog", "article", "admin", "n/a", "none"}


@dataclass
class CredibilityResult:
    """Structured output for source credibility assessment."""

    domain: str
    domain_type: str
    uses_https: bool
    domain_transparency_score: float
    publisher_identifiability_score: float
    author_attribution_score: float
    temporal_transparency_score: float
    reference_support_score: float
    automated_credibility_score: float
    manual_adjustment: float
    final_credibility_score: float
    reviewer_explanation: str = ""
    signals: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize credibility assessment to a dictionary."""
        return {
            "domain": self.domain,
            "domain_type": self.domain_type,
            "uses_https": self.uses_https,
            "domain_transparency_score": self.domain_transparency_score,
            "publisher_identifiability_score": self.publisher_identifiability_score,
            "author_attribution_score": self.author_attribution_score,
            "temporal_transparency_score": self.temporal_transparency_score,
            "reference_support_score": self.reference_support_score,
            "automated_credibility_score": self.automated_credibility_score,
            "manual_adjustment": self.manual_adjustment,
            "final_credibility_score": self.final_credibility_score,
            "reviewer_explanation": self.reviewer_explanation,
            "signals": self.signals,
            "cautions": self.cautions,
        }


def _classify_domain_type(hostname: str) -> str:
    """Classify domain suffix descriptively without treating any TLD as infallible."""
    lower = hostname.lower()
    for suffix, label in DOMAIN_CATEGORIES.items():
        if lower.endswith(suffix) or f"{suffix}." in lower:
            return label
    return "General / Other Domain"


def assess_source_credibility(
    url: str,
    source_name: str = "",
    author: str = "",
    published_date: str = "",
    supporting_evidence: str = "",
    reference_urls: list[str] | None = None,
    manual_adjustment: float = 0.0,
    reviewer_explanation: str = "",
) -> CredibilityResult:
    """Assess source credibility using transparent metadata signals and optional manual adjustment.

    Note: Domain suffixes (.gov, .edu, .org) are treated strictly as contextual descriptors
    and never automatically guarantee trustworthiness or factual accuracy.
    """
    clean_url = sanitize_text(url)
    clean_source = sanitize_text(source_name)
    clean_author = sanitize_text(author)
    clean_date = sanitize_text(published_date)
    clean_evidence = sanitize_text(supporting_evidence)
    clean_explanation = sanitize_text(reviewer_explanation)
    refs = [sanitize_text(r) for r in (reference_urls or []) if sanitize_text(r)]

    signals: list[str] = []
    cautions: list[str] = [
        "Domain suffix (e.g., .gov, .edu) only indicates registration category, not guaranteed accuracy or impartiality."
    ]

    parsed = urlparse(clean_url)
    hostname = (parsed.hostname or "").lower()
    uses_https = parsed.scheme.lower() == "https"
    domain_type = _classify_domain_type(hostname) if hostname else "Unidentified Domain"

    # 1. Domain & transport transparency (0-100) — neutral across TLDs
    url_ok, _ = validate_url(clean_url)
    if not url_ok:
        domain_score = 15.0
        cautions.append("URL failed structural validation; domain transparency severely limited.")
    else:
        domain_score = 55.0
        if uses_https:
            domain_score += 25.0
            signals.append("Uses HTTPS transport encryption.")
        else:
            cautions.append("Uses unencrypted HTTP rather than HTTPS.")
        if hostname.count(".") <= 3 and len(hostname) <= 60:
            domain_score += 10.0
        if any(flag in hostname for flag in ("free-news", "click", "promo", "ads")):
            domain_score -= 20.0
            cautions.append("Hostname contains promotional or low-trust naming patterns.")
    domain_score = round(float(np.clip(domain_score, 0.0, 100.0)), 2)

    # 2. Publisher identifiability (0-100)
    if not clean_source or clean_source.lower() in GENERIC_SOURCE_NAMES:
        publisher_score = 20.0
        cautions.append("Identifiable publisher name is missing or overly generic.")
    else:
        publisher_score = 75.0
        signals.append(f"Publisher identified as '{clean_source}'.")
        # Check mild consistency between source name tokens and domain
        source_tokens = [tok for tok in clean_source.lower().split() if len(tok) >= 3]
        if hostname and any(tok in hostname for tok in source_tokens):
            publisher_score += 20.0
            signals.append("Publisher name aligns clearly with domain host.")
        else:
            publisher_score += 10.0
    publisher_score = round(float(np.clip(publisher_score, 0.0, 100.0)), 2)

    # 3. Author attribution (0-100)
    if clean_author and clean_author.lower() not in GENERIC_SOURCE_NAMES:
        author_score = 90.0
        signals.append(f"Author attribution provided: {clean_author}.")
    else:
        author_score = 35.0
        cautions.append("No individual author or editorial team supplied; check institutional accountability manually.")

    # 4. Publication date transparency (0-100)
    date_ok, date_msg = validate_date_string(clean_date)
    if clean_date and date_ok:
        pub_dt = datetime.strptime(clean_date, "%Y-%m-%d").date()
        age_days = (datetime.today().date() - pub_dt).days
        if age_days <= 365 * 2:
            temporal_score = 95.0
            signals.append(f"Recent publication date provided ({clean_date}).")
        elif age_days <= 365 * 5:
            temporal_score = 75.0
            signals.append(f"Publication date provided ({clean_date}); verify whether newer updates exist.")
        else:
            temporal_score = 50.0
            cautions.append(f"Published {clean_date} (>5 years ago); information may be outdated.")
    elif clean_date and not date_ok:
        temporal_score = 25.0
        cautions.append(date_msg)
    else:
        temporal_score = 30.0
        cautions.append("Publication date not supplied; content currency cannot be verified.")

    # 5. Supporting references / evidence (0-100)
    valid_refs = [ref for ref in refs if validate_url(ref)[0]]
    if valid_refs and clean_evidence:
        reference_score = 95.0
        signals.append(f"Includes supporting evidence and {len(valid_refs)} valid reference URL(s).")
    elif valid_refs:
        reference_score = 80.0
        signals.append(f"Includes {len(valid_refs)} valid reference URL(s).")
    elif clean_evidence:
        reference_score = 65.0
        signals.append("Includes supporting evidence text; add direct reference URLs for stronger auditability.")
    else:
        reference_score = 20.0
        cautions.append("No supporting references or evidence notes supplied.")

    automated_score = round(
        float(
            np.clip(
                0.25 * domain_score
                + 0.25 * publisher_score
                + 0.15 * author_score
                + 0.15 * temporal_score
                + 0.20 * reference_score,
                0.0,
                100.0,
            )
        ),
        2,
    )

    clamped_adj = round(float(np.clip(manual_adjustment, -40.0, 40.0)), 2)
    final_score = round(float(np.clip(automated_score + clamped_adj, 0.0, 100.0)), 2)

    if clamped_adj != 0.0:
        sign = "+" if clamped_adj > 0 else ""
        signals.append(f"Manual reviewer credibility adjustment applied: {sign}{clamped_adj}.")

    return CredibilityResult(
        domain=hostname or "N/A",
        domain_type=domain_type,
        uses_https=uses_https,
        domain_transparency_score=domain_score,
        publisher_identifiability_score=publisher_score,
        author_attribution_score=author_score,
        temporal_transparency_score=temporal_score,
        reference_support_score=reference_score,
        automated_credibility_score=automated_score,
        manual_adjustment=clamped_adj,
        final_credibility_score=final_score,
        reviewer_explanation=clean_explanation,
        signals=signals,
        cautions=cautions,
    )
