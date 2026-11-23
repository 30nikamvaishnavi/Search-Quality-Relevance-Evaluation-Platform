"""Search relevance and rule-based intent alignment evaluation using TF-IDF."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.validators import sanitize_text

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}

INFORMATIONAL_CUES = {
    "how",
    "what",
    "why",
    "when",
    "where",
    "who",
    "guide",
    "tutorial",
    "explain",
    "definition",
    "meaning",
    "overview",
    "symptoms",
    "causes",
    "prevention",
    "basics",
    "examples",
    "difference",
    "vs",
}

NAVIGATIONAL_CUES = {
    "official",
    "portal",
    "login",
    "homepage",
    "website",
    "site",
    "docs",
    "documentation",
    "form",
    "application",
    "apply",
    "deadline",
    "deadlines",
}

TRANSACTIONAL_CUES = {
    "buy",
    "price",
    "pricing",
    "cost",
    "download",
    "install",
    "best",
    "top",
    "compare",
    "comparison",
    "review",
    "software",
    "tool",
    "service",
    "plan",
}

TIMELY_CUES = {
    "2024",
    "2025",
    "2026",
    "latest",
    "recent",
    "update",
    "updates",
    "news",
    "announcement",
    "new",
    "current",
    "program",
    "programs",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")

RELEVANCE_DISCLAIMER = (
    "Automated TF-IDF similarity and rule-based intent scores measure lexical and "
    "structural alignment only; they do not establish factual truth."
)


@dataclass
class RelevanceResult:
    """Structured output for search relevance evaluation."""

    query_title_similarity: float
    query_description_similarity: float
    keyword_overlap_score: float
    intent_alignment_score: float
    overall_relevance_score: float
    detected_intent: str
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    intent_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = RELEVANCE_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        """Convert evaluation result to a JSON-serializable dictionary."""
        return {
            "query_title_similarity": self.query_title_similarity,
            "query_description_similarity": self.query_description_similarity,
            "keyword_overlap_score": self.keyword_overlap_score,
            "intent_alignment_score": self.intent_alignment_score,
            "overall_relevance_score": self.overall_relevance_score,
            "detected_intent": self.detected_intent,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "intent_reasons": self.intent_reasons,
            "warnings": self.warnings,
            "disclaimer": self.disclaimer,
        }


def _tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    tokens = TOKEN_RE.findall(text.lower())
    if remove_stopwords:
        return [tok for tok in tokens if tok not in STOP_WORDS]
    return tokens


def compute_tfidf_cosine(text_a: str, text_b: str) -> float:
    """Compute TF-IDF cosine similarity between two strings scaled to 0-100."""
    clean_a = sanitize_text(text_a)
    clean_b = sanitize_text(text_b)
    if not clean_a or not clean_b:
        return 0.0

    # Use token pattern that preserves single-character/numeric tokens safely
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z0-9]+\b",
        sublinear_tf=True,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([clean_a, clean_b])
    except ValueError:
        return 0.0

    sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    raw_score = float(np.clip(sim_matrix[0, 0], 0.0, 1.0))
    return round(raw_score * 100.0, 2)


def detect_query_intent(query: str) -> str:
    """Classify search query intent using transparent keyword rules."""
    tokens = set(_tokenize(sanitize_text(query), remove_stopwords=False))
    if not tokens:
        return "general"

    scores = {
        "informational": len(tokens & INFORMATIONAL_CUES),
        "navigational": len(tokens & NAVIGATIONAL_CUES),
        "transactional": len(tokens & TRANSACTIONAL_CUES),
        "timely": len(tokens & TIMELY_CUES),
    }

    best_intent = max(scores, key=lambda key: scores[key])
    if scores[best_intent] == 0:
        return "informational"
    return best_intent


def evaluate_intent_alignment(
    query: str,
    title: str,
    description: str,
    url: str = "",
    source_name: str = "",
    published_date: str = "",
) -> tuple[float, str, list[str]]:
    """Evaluate alignment between detected query intent and result signals."""
    intent = detect_query_intent(query)
    combined_lower = f"{title} {description} {source_name}".lower()
    combined_tokens = set(_tokenize(combined_lower, remove_stopwords=False))
    query_tokens = set(_tokenize(query, remove_stopwords=True))
    if not query_tokens:
        query_tokens = set(_tokenize(query, remove_stopwords=False))

    reasons: list[str] = []
    if not query_tokens:
        return 0.0, "general", ["Query has no analyzable terms for intent matching."]

    coverage = len(query_tokens & combined_tokens) / max(len(query_tokens), 1)
    base_score = 45.0 * coverage

    if intent == "informational":
        info_signals = {"guide", "overview", "how", "steps", "explain", "basics", "definition", "summary", "process", "guidelines"}
        hits = sorted(combined_tokens & info_signals)
        if hits:
            base_score += 30.0
            reasons.append(f"Informational cues found in snippet/title: {', '.join(hits)}.")
        else:
            reasons.append("Query seeks explanation/information; limited explicit guide cues detected.")
        if len(description.split()) >= 18:
            base_score += 25.0
            reasons.append("Snippet provides substantive explanatory context (>= 18 words).")
        elif description:
            base_score += 10.0
            reasons.append("Snippet is brief; partial informational depth.")

    elif intent == "navigational":
        nav_signals = {"official", "portal", "documentation", "docs", "guidelines", "application", "form", "site"}
        hits = sorted(combined_tokens & nav_signals)
        if hits:
            base_score += 30.0
            reasons.append(f"Navigational/official cues matched: {', '.join(hits)}.")
        if source_name.strip() and any(tok in source_name.lower() for tok in query_tokens):
            base_score += 25.0
            reasons.append("Source name directly matches query entity terms.")
        elif url.strip():
            base_score += 10.0
            reasons.append("Destination URL present, though source name does not explicitly mirror query.")

    elif intent == "transactional":
        trans_signals = {"compare", "comparison", "features", "pricing", "options", "tool", "guide", "checklist", "requirements"}
        hits = sorted(combined_tokens & trans_signals)
        if hits:
            base_score += 35.0
            reasons.append(f"Decision/actionable cues present: {', '.join(hits)}.")
        else:
            reasons.append("Limited comparison or actionable evaluation signals in snippet.")
        if len(description.split()) >= 15:
            base_score += 20.0
            reasons.append("Snippet offers concrete details to support user action.")

    elif intent == "timely":
        timely_signals = {"2024", "2025", "2026", "update", "updated", "new", "recent", "current", "announced", "program"}
        hits = sorted(combined_tokens & timely_signals)
        if hits:
            base_score += 30.0
            reasons.append(f"Timely/currency cues present: {', '.join(hits)}.")
        if sanitize_text(published_date):
            base_score += 25.0
            reasons.append(f"Publication date provided ({published_date}) supporting temporal verification.")
        else:
            reasons.append("No publication date provided for a time-sensitive query.")

    score = round(float(np.clip(base_score, 0.0, 100.0)), 2)
    return score, intent, reasons


def evaluate_relevance(
    query: str,
    title: str,
    description: str,
    url: str = "",
    source_name: str = "",
    published_date: str = "",
) -> RelevanceResult:
    """Evaluate search result relevance against a user query."""
    clean_query = sanitize_text(query)
    clean_title = sanitize_text(title)
    clean_desc = sanitize_text(description)
    clean_source = sanitize_text(source_name)
    clean_date = sanitize_text(published_date)
    warnings: list[str] = []

    if not clean_query:
        return RelevanceResult(
            query_title_similarity=0.0,
            query_description_similarity=0.0,
            keyword_overlap_score=0.0,
            intent_alignment_score=0.0,
            overall_relevance_score=0.0,
            detected_intent="general",
            intent_reasons=["Cannot evaluate intent without a search query."],
            warnings=["Search query is empty; all relevance scores set to 0."],
        )

    if not clean_title:
        warnings.append("Result title is missing; query-title similarity set to 0.")
    if not clean_desc:
        warnings.append("Description/snippet is missing; description similarity set to 0.")

    title_sim = compute_tfidf_cosine(clean_query, clean_title)
    desc_sim = compute_tfidf_cosine(clean_query, clean_desc)

    query_terms = _tokenize(clean_query, remove_stopwords=True)
    if not query_terms:
        query_terms = _tokenize(clean_query, remove_stopwords=False)
    unique_query_terms = list(dict.fromkeys(query_terms))

    result_terms = set(_tokenize(f"{clean_title} {clean_desc}", remove_stopwords=True))
    if not result_terms:
        result_terms = set(_tokenize(f"{clean_title} {clean_desc}", remove_stopwords=False))

    matched = [term for term in unique_query_terms if term in result_terms]
    missing = [term for term in unique_query_terms if term not in result_terms]

    if unique_query_terms:
        query_coverage = len(matched) / len(unique_query_terms)
        union_count = len(set(unique_query_terms) | result_terms)
        jaccard = len(set(unique_query_terms) & result_terms) / max(union_count, 1)
        keyword_overlap = round(float(np.clip((0.75 * query_coverage + 0.25 * jaccard) * 100.0, 0.0, 100.0)), 2)
    else:
        keyword_overlap = 0.0

    intent_score, detected_intent, intent_reasons = evaluate_intent_alignment(
        query=clean_query,
        title=clean_title,
        description=clean_desc,
        url=url,
        source_name=clean_source,
        published_date=clean_date,
    )

    overall = round(
        float(
            np.clip(
                0.35 * title_sim
                + 0.30 * desc_sim
                + 0.20 * keyword_overlap
                + 0.15 * intent_score,
                0.0,
                100.0,
            )
        ),
        2,
    )

    return RelevanceResult(
        query_title_similarity=title_sim,
        query_description_similarity=desc_sim,
        keyword_overlap_score=keyword_overlap,
        intent_alignment_score=intent_score,
        overall_relevance_score=overall,
        detected_intent=detected_intent,
        matched_keywords=matched,
        missing_keywords=missing,
        intent_reasons=intent_reasons,
        warnings=warnings,
    )
