"""Content quality evaluation covering completeness, readability, usefulness, and repetition."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.evaluator.relevance import STOP_WORDS
from src.utils.validators import sanitize_text

WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")

CLICKBAIT_PHRASES = (
    "you won't believe",
    "shocking secret",
    "miracle cure",
    "doctors hate",
    "click here now",
    "100% guaranteed",
    "mind blowing",
    "secret trick",
)


@dataclass
class ContentQualityResult:
    """Structured content quality evaluation output."""

    completeness_score: float
    readability_score: float
    keyword_relevance_score: float
    usefulness_score: float
    uniqueness_score: float
    overall_quality_score: float
    word_count: int
    explanations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize content quality result to a dictionary."""
        return {
            "completeness_score": self.completeness_score,
            "readability_score": self.readability_score,
            "keyword_relevance_score": self.keyword_relevance_score,
            "usefulness_score": self.usefulness_score,
            "uniqueness_score": self.uniqueness_score,
            "overall_quality_score": self.overall_quality_score,
            "word_count": self.word_count,
            "explanations": self.explanations,
            "warnings": self.warnings,
        }


def _count_syllables(word: str) -> int:
    """Estimate syllable count for readability calculation."""
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if not cleaned:
        return 1
    if len(cleaned) <= 3:
        return 1
    cleaned = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", cleaned)
    cleaned = re.sub(r"^y", "", cleaned)
    vowels = re.findall(r"[aeiouy]{1,2}", cleaned)
    return max(1, len(vowels))


def evaluate_content_quality(
    query: str,
    title: str,
    description: str,
    source_name: str = "",
    published_date: str = "",
    supporting_evidence: str = "",
) -> ContentQualityResult:
    """Evaluate search result content quality with transparent explanations."""
    clean_query = sanitize_text(query)
    clean_title = sanitize_text(title)
    clean_desc = sanitize_text(description)
    clean_source = sanitize_text(source_name)
    clean_date = sanitize_text(published_date)
    clean_evidence = sanitize_text(supporting_evidence)

    explanations: list[str] = []
    warnings: list[str] = []

    words = WORD_RE.findall(clean_desc)
    word_count = len(words)

    # 1. Completeness (0-100)
    completeness = 0.0
    if clean_title:
        completeness += 20.0
    else:
        warnings.append("Missing title lowers completeness.")

    if word_count >= 30:
        completeness += 40.0
        explanations.append(f"Snippet has strong length ({word_count} words) for context assessment.")
    elif word_count >= 15:
        completeness += 28.0
        explanations.append(f"Snippet has moderate length ({word_count} words).")
    elif word_count > 0:
        completeness += 14.0
        warnings.append(f"Snippet is very short ({word_count} words); limited context available.")
    else:
        warnings.append("Description/snippet is missing; completeness and readability are penalized.")

    if clean_source:
        completeness += 15.0
    if clean_date:
        completeness += 10.0
    if clean_evidence:
        completeness += 15.0
        explanations.append("Supporting evidence text was provided alongside the result.")

    completeness = round(float(np.clip(completeness, 0.0, 100.0)), 2)

    # 2. Readability (0-100)
    if word_count == 0:
        readability = 0.0
    else:
        sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(clean_desc) if s.strip()]
        num_sentences = max(1, len(sentences))
        avg_sentence_len = word_count / num_sentences
        total_syllables = sum(_count_syllables(w) for w in words)
        avg_syllables = total_syllables / word_count

        # Flesch Reading Ease normalized gently into 0-100
        flesch = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables
        readability_raw = np.clip(flesch, 15.0, 95.0)
        # Penalize all-caps shouting or very long unpunctuated run-ons
        alpha_chars = [ch for ch in clean_desc if ch.isalpha()]
        upper_ratio = sum(1 for ch in alpha_chars if ch.isupper()) / max(len(alpha_chars), 1)
        if upper_ratio > 0.55 and len(alpha_chars) > 12:
            readability_raw -= 25.0
            warnings.append("Excessive uppercase text reduces readability.")
        if avg_sentence_len > 35:
            readability_raw -= 12.0
            warnings.append("Long average sentence length reduces snippet readability.")

        readability = round(float(np.clip(readability_raw, 0.0, 100.0)), 2)
        explanations.append(
            f"Readability estimated at {readability}/100 (avg {avg_sentence_len:.1f} words/sentence)."
        )

    # 3. Keyword Relevance & Anti-Stuffing (0-100)
    query_terms = [w.lower() for w in WORD_RE.findall(clean_query) if w.lower() not in STOP_WORDS]
    content_terms = [w.lower() for w in WORD_RE.findall(f"{clean_title} {clean_desc}") if w.lower() not in STOP_WORDS]

    if not query_terms or not content_terms:
        keyword_relevance = 0.0
    else:
        unique_q = set(query_terms)
        unique_c = set(content_terms)
        coverage = len(unique_q & unique_c) / len(unique_q)
        term_counts = Counter(content_terms)
        max_freq_ratio = max(term_counts.values()) / len(content_terms)

        keyword_relevance = coverage * 100.0
        if max_freq_ratio > 0.22 and len(content_terms) >= 10:
            keyword_relevance -= 30.0
            warnings.append("Potential keyword stuffing detected (high single-term concentration).")
        keyword_relevance = round(float(np.clip(keyword_relevance, 0.0, 100.0)), 2)

    # 4. Uniqueness / Anti-Repetition (0-100)
    if word_count == 0:
        uniqueness = 0.0
    else:
        lower_words = [w.lower() for w in words]
        type_token_ratio = len(set(lower_words)) / len(lower_words)
        uniqueness_raw = 40.0 + 60.0 * min(type_token_ratio / 0.75, 1.0)

        # Penalize if description is virtually identical to title
        if clean_title and clean_desc.lower() == clean_title.lower():
            uniqueness_raw -= 45.0
            warnings.append("Description merely duplicates the title without new information.")

        # Penalize repeated sentences
        sentences_lower = [s.strip().lower() for s in SENTENCE_SPLIT_RE.split(clean_desc) if s.strip()]
        if len(sentences_lower) > 1 and len(set(sentences_lower)) < len(sentences_lower):
            uniqueness_raw -= 25.0
            warnings.append("Repetitive sentences detected in description.")

        uniqueness = round(float(np.clip(uniqueness_raw, 0.0, 100.0)), 2)

    # 5. Usefulness (0-100)
    if word_count == 0:
        usefulness = 0.0
    else:
        usefulness_raw = 35.0
        if word_count >= 20:
            usefulness_raw += 25.0
        elif word_count >= 10:
            usefulness_raw += 12.0

        # Concrete informational markers: numbers, years, structured explanations, evidence
        has_numbers = bool(re.search(r"\d+", clean_desc))
        informative_verbs = {"explains", "covers", "includes", "provides", "outlines", "compares", "shows", "describes", "lists", "details", "requires", "recommends"}
        has_informative_markers = bool(set(w.lower() for w in words) & informative_verbs)

        if has_numbers:
            usefulness_raw += 15.0
            explanations.append("Contains concrete quantitative or dated details.")
        if has_informative_markers:
            usefulness_raw += 15.0
            explanations.append("Uses specific explanatory language.")
        if clean_evidence:
            usefulness_raw += 10.0

        lower_full = f"{clean_title} {clean_desc}".lower()
        found_clickbait = [phrase for phrase in CLICKBAIT_PHRASES if phrase in lower_full]
        if found_clickbait:
            usefulness_raw -= 35.0
            warnings.append(f"Sensational/clickbait phrasing detected: {', '.join(found_clickbait)}.")

        usefulness = round(float(np.clip(usefulness_raw, 0.0, 100.0)), 2)

    overall_quality = round(
        float(
            np.clip(
                0.25 * completeness
                + 0.20 * readability
                + 0.20 * keyword_relevance
                + 0.20 * usefulness
                + 0.15 * uniqueness,
                0.0,
                100.0,
            )
        ),
        2,
    )

    return ContentQualityResult(
        completeness_score=completeness,
        readability_score=readability,
        keyword_relevance_score=keyword_relevance,
        usefulness_score=usefulness,
        uniqueness_score=uniqueness,
        overall_quality_score=overall_quality,
        word_count=word_count,
        explanations=explanations,
        warnings=warnings,
    )
