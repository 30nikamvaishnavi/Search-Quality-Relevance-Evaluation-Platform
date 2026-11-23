"""CSV and JSON report export utilities with safe formula-injection neutralization."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_csv_value(value: Any) -> Any:
    """Neutralize spreadsheet formula injection in exported string fields."""
    if isinstance(value, str) and value and value[0] in FORMULA_PREFIXES:
        return f"'{value}"
    return value


def _sanitize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply safe CSV sanitization across all row dictionaries."""
    return [{k: _safe_csv_value(v) for k, v in row.items()} for row in rows]


def export_summary_csv(evaluations: list[dict[str, Any]]) -> str:
    """Export an overall summary table of evaluation sessions to CSV format."""
    rows: list[dict[str, Any]] = []
    for item in evaluations:
        metrics = item.get("summary_metrics", {})
        fact_summary = item.get("fact_summary", {})
        rows.append(
            {
                "evaluation_id": item.get("evaluation_id", ""),
                "created_at": item.get("created_at", ""),
                "query": item.get("query", ""),
                "category": item.get("category", ""),
                "reviewer_name": item.get("reviewer_name", ""),
                "total_results": metrics.get("total_results", 0),
                "avg_relevance_score": metrics.get("avg_relevance_score", 0.0),
                "avg_content_quality_score": metrics.get("avg_content_quality_score", 0.0),
                "avg_overall_score": metrics.get("avg_overall_score", 0.0),
                "top_result_title": metrics.get("top_result_title", ""),
                "top_result_score": metrics.get("top_result_score", 0.0),
                "supported_claims": fact_summary.get("supported_count", 0),
                "contradicted_claims": fact_summary.get("contradicted_count", 0),
                "unverified_claims": fact_summary.get("unverified_count", 0),
                "is_synthetic": item.get("is_synthetic", False),
            }
        )

    columns = [
        "evaluation_id",
        "created_at",
        "query",
        "category",
        "reviewer_name",
        "total_results",
        "avg_relevance_score",
        "avg_content_quality_score",
        "avg_overall_score",
        "top_result_title",
        "top_result_score",
        "supported_claims",
        "contradicted_claims",
        "unverified_claims",
        "is_synthetic",
    ]
    df = pd.DataFrame(_sanitize_rows(rows), columns=columns)
    return df.to_csv(index=False)


def export_results_csv(evaluation: dict[str, Any]) -> str:
    """Export individual search result assessments from a single evaluation to CSV."""
    rows: list[dict[str, Any]] = []
    eval_id = evaluation.get("evaluation_id", "")
    query = evaluation.get("query", "")

    for res in evaluation.get("results", []):
        rel = res.get("relevance", {})
        qual = res.get("content_quality", {})
        cred = res.get("credibility", {})
        overall = res.get("overall", {})
        rows.append(
            {
                "evaluation_id": eval_id,
                "query": query,
                "result_id": res.get("result_id", ""),
                "title": res.get("title", ""),
                "url": res.get("url", ""),
                "source_name": res.get("source_name", ""),
                "published_date": res.get("published_date", ""),
                "detected_intent": rel.get("detected_intent", ""),
                "query_title_similarity": rel.get("query_title_similarity", 0.0),
                "query_description_similarity": rel.get("query_description_similarity", 0.0),
                "keyword_overlap_score": rel.get("keyword_overlap_score", 0.0),
                "intent_alignment_score": rel.get("intent_alignment_score", 0.0),
                "overall_relevance_score": rel.get("overall_relevance_score", 0.0),
                "content_quality_score": qual.get("overall_quality_score", 0.0),
                "automated_credibility_score": cred.get("automated_credibility_score", 0.0),
                "final_credibility_score": cred.get("final_credibility_score", 0.0),
                "automated_overall_score": overall.get("automated_score", 0.0),
                "final_display_score": overall.get("final_display_score", 0.0),
                "score_source": overall.get("score_source", ""),
                "evidence_status": overall.get("evidence_status", ""),
                "human_label": overall.get("human_label") or "",
                "human_comments": overall.get("human_comments") or "",
            }
        )

    columns = [
        "evaluation_id",
        "query",
        "result_id",
        "title",
        "url",
        "source_name",
        "published_date",
        "detected_intent",
        "query_title_similarity",
        "query_description_similarity",
        "keyword_overlap_score",
        "intent_alignment_score",
        "overall_relevance_score",
        "content_quality_score",
        "automated_credibility_score",
        "final_credibility_score",
        "automated_overall_score",
        "final_display_score",
        "score_source",
        "evidence_status",
        "human_label",
        "human_comments",
    ]
    df = pd.DataFrame(_sanitize_rows(rows), columns=columns)
    return df.to_csv(index=False)


def export_evaluation_json(evaluation: dict[str, Any]) -> str:
    """Export a single detailed evaluation record as pretty-printed JSON."""
    return json.dumps(evaluation, indent=2, ensure_ascii=False)


def export_all_evaluations_json(evaluations: list[dict[str, Any]]) -> str:
    """Export multiple evaluation records as a JSON array string."""
    return json.dumps(evaluations, indent=2, ensure_ascii=False)
