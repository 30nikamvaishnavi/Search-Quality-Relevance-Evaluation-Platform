"""Input validation, sanitization, URL checking, and duplicate detection utilities."""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse, urlunparse

ALLOWED_URL_SCHEMES = {"http", "https"}
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")


def sanitize_text(text: str | None) -> str:
    """Safely normalize optional text by stripping control characters and trimming whitespace."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    cleaned = CONTROL_CHARS_RE.sub("", text)
    return cleaned.strip()


def validate_query(query: str | None) -> tuple[bool, str]:
    """Validate a search query string."""
    cleaned = sanitize_text(query)
    if not cleaned:
        return False, "Search query cannot be empty."
    if len(cleaned) < 2:
        return False, "Search query must be at least 2 characters long."
    if len(cleaned) > 500:
        return False, "Search query cannot exceed 500 characters."
    return True, "Valid search query."


def validate_url(url: str | None) -> tuple[bool, str]:
    """Validate that a URL uses http/https and has a well-formed host."""
    cleaned = sanitize_text(url)
    if not cleaned:
        return False, "URL cannot be empty."
    if any(ch.isspace() for ch in cleaned):
        return False, "URL must not contain whitespace characters."

    parsed = urlparse(cleaned)
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_URL_SCHEMES:
        return False, "URL must start with http:// or https://."
    if not parsed.netloc:
        return False, "URL must include a valid domain host."

    hostname = parsed.hostname or ""
    if not hostname:
        return False, "URL hostname is invalid."
    if hostname != "localhost" and "." not in hostname:
        return False, "URL domain must include a top-level domain (e.g., .org, .com, .edu)."
    if hostname.startswith(".") or hostname.endswith(".") or ".." in hostname:
        return False, "URL domain format is invalid."

    return True, "Valid URL."


def normalize_url(url: str | None) -> str:
    """Normalize a URL for reliable duplicate detection."""
    cleaned = sanitize_text(url)
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def validate_date_string(date_str: str | None) -> tuple[bool, str]:
    """Validate an optional publication date string (ISO YYYY-MM-DD)."""
    cleaned = sanitize_text(date_str)
    if not cleaned:
        return True, "No publication date provided."
    try:
        parsed_date = datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        return False, "Published date must follow YYYY-MM-DD format (e.g., 2025-04-15)."

    if parsed_date > date.today():
        return False, "Published date cannot be in the future."
    return True, "Valid date."


def validate_score(
    score: float | int | None,
    min_val: float = 0.0,
    max_val: float = 100.0,
) -> tuple[bool, str]:
    """Validate that a numeric score is finite and within bounds."""
    if score is None or isinstance(score, bool):
        return False, "Score must be a valid number."
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return False, "Score must be numeric."
    if math.isnan(numeric) or math.isinf(numeric):
        return False, "Score must be a finite number."
    if numeric < min_val or numeric > max_val:
        return False, f"Score must be between {min_val:.0f} and {max_val:.0f}."
    return True, "Valid score."


def validate_search_result(result: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a single search result entry and return (is_valid, error_messages)."""
    errors: list[str] = []
    title = sanitize_text(result.get("title"))
    url = sanitize_text(result.get("url"))
    description = sanitize_text(result.get("description"))
    source_name = sanitize_text(result.get("source_name"))
    published_date = sanitize_text(result.get("published_date"))

    if not title:
        errors.append("Result title is required.")
    url_ok, url_msg = validate_url(url)
    if not url_ok:
        errors.append(url_msg)
    if not description:
        errors.append("Result description/snippet is required.")
    if not source_name:
        errors.append("Source name is required.")

    date_ok, date_msg = validate_date_string(published_date)
    if not date_ok:
        errors.append(date_msg)

    return len(errors) == 0, errors


def detect_duplicate_results(results: list[dict[str, Any]]) -> list[tuple[int, int, str]]:
    """Detect duplicate search results by normalized URL or identical (title, source_name).

    Returns a list of (first_index, duplicate_index, reason).
    """
    seen_urls: dict[str, int] = {}
    seen_title_source: dict[tuple[str, str], int] = {}
    duplicates: list[tuple[int, int, str]] = []

    for idx, item in enumerate(results):
        norm_url = normalize_url(item.get("url"))
        norm_title = WHITESPACE_RE.sub(" ", sanitize_text(item.get("title")).lower())
        norm_source = WHITESPACE_RE.sub(" ", sanitize_text(item.get("source_name")).lower())

        if norm_url and norm_url in seen_urls:
            duplicates.append((seen_urls[norm_url], idx, f"Duplicate URL: {norm_url}"))
            continue
        if norm_url:
            seen_urls[norm_url] = idx

        key = (norm_title, norm_source)
        if norm_title and key in seen_title_source:
            duplicates.append(
                (seen_title_source[key], idx, f"Duplicate title and source: '{item.get('title', '')}'")
            )
            continue
        if norm_title:
            seen_title_source[key] = idx

    return duplicates
