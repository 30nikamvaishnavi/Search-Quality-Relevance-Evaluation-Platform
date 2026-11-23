"""End-to-end evaluation pipeline orchestrating relevance, quality, credibility, facts, and scoring."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.evaluator.content_quality import evaluate_content_quality
from src.evaluator.credibility import assess_source_credibility
from src.evaluator.fact_checker import summarize_fact_checks
from src.evaluator.relevance import evaluate_relevance
from src.evaluator.scoring import DEFAULT_WEIGHTS, compute_overall_score, normalize_weights
from src.utils.validators import detect_duplicate_results, sanitize_text


def evaluate_single_result(
    query: str,
    result_item: dict[str, Any],
    claims: list[dict[str, Any]] | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Run all evaluation modules on a single search result and return a complete assessment dict."""
    title = sanitize_text(result_item.get("title"))
    url = sanitize_text(result_item.get("url"))
    description = sanitize_text(result_item.get("description"))
    source_name = sanitize_text(result_item.get("source_name"))
    published_date = sanitize_text(result_item.get("published_date"))
    supporting_evidence = sanitize_text(result_item.get("supporting_evidence"))
    author = sanitize_text(result_item.get("author"))
    reference_urls = result_item.get("reference_urls") or []
    manual_cred_adj = float(result_item.get("manual_credibility_adjustment", 0.0) or 0.0)
    cred_explanation = sanitize_text(result_item.get("credibility_explanation"))

    relevance_res = evaluate_relevance(
        query=query,
        title=title,
        description=description,
        url=url,
        source_name=source_name,
        published_date=published_date,
    )
    quality_res = evaluate_content_quality(
        query=query,
        title=title,
        description=description,
        source_name=source_name,
        published_date=published_date,
        supporting_evidence=supporting_evidence,
    )
    credibility_res = assess_source_credibility(
        url=url,
        source_name=source_name,
        author=author,
        published_date=published_date,
        supporting_evidence=supporting_evidence,
        reference_urls=reference_urls,
        manual_adjustment=manual_cred_adj,
        reviewer_explanation=cred_explanation,
    )

    # Filter claims linked to this result title if provided, else use global claims if linked
    linked_claims = [
        c for c in (claims or [])
        if not sanitize_text(c.get("result_title"))
        or sanitize_text(c.get("result_title")).lower() == title.lower()
    ]
    fact_summary = summarize_fact_checks(linked_claims)

    overall_res = compute_overall_score(
        search_relevance=relevance_res.overall_relevance_score,
        content_quality=quality_res.overall_quality_score,
        source_credibility=credibility_res.final_credibility_score,
        intent_alignment=relevance_res.intent_alignment_score,
        factual_evidence=fact_summary["factual_evidence_score"],
        has_adequate_evidence=fact_summary["has_adequate_evidence"],
        weights=weights,
        human_label=result_item.get("human_label"),
        human_score_override=result_item.get("human_score_override"),
        human_comments=sanitize_text(result_item.get("human_comments")),
    )

    return {
        "result_id": result_item.get("result_id") or f"res-{uuid.uuid4().hex[:8]}",
        "title": title,
        "url": url,
        "description": description,
        "source_name": source_name,
        "author": author,
        "published_date": published_date,
        "supporting_evidence": supporting_evidence,
        "reference_urls": reference_urls,
        "relevance": relevance_res.to_dict(),
        "content_quality": quality_res.to_dict(),
        "credibility": credibility_res.to_dict(),
        "fact_summary": fact_summary,
        "overall": overall_res.to_dict(),
    }


def evaluate_search_session(
    query: str,
    results: list[dict[str, Any]],
    claims: list[dict[str, Any]] | None = None,
    weights: dict[str, float] | None = None,
    category: str = "General",
    reviewer_name: str = "Analyst",
    session_notes: str = "",
    is_synthetic: bool = False,
    evaluation_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate a query and its list of search results into a storable evaluation record."""
    clean_query = sanitize_text(query)
    norm_weights = normalize_weights(weights or DEFAULT_WEIGHTS)
    claim_list = list(claims or [])

    duplicates = detect_duplicate_results(results)
    evaluated_results = [
        evaluate_single_result(
            query=clean_query,
            result_item=item,
            claims=claim_list,
            weights=norm_weights,
        )
        for item in results
    ]

    # Sort copy by final_display_score descending to identify top ranked
    ranked = sorted(
        evaluated_results,
        key=lambda r: r["overall"]["final_display_score"],
        reverse=True,
    )

    avg_relevance = (
        round(
            sum(r["relevance"]["overall_relevance_score"] for r in evaluated_results)
            / len(evaluated_results),
            2,
        )
        if evaluated_results
        else 0.0
    )
    avg_quality = (
        round(
            sum(r["content_quality"]["overall_quality_score"] for r in evaluated_results)
            / len(evaluated_results),
            2,
        )
        if evaluated_results
        else 0.0
    )
    avg_overall = (
        round(
            sum(r["overall"]["final_display_score"] for r in evaluated_results)
            / len(evaluated_results),
            2,
        )
        if evaluated_results
        else 0.0
    )

    global_fact_summary = summarize_fact_checks(claim_list)

    return {
        "evaluation_id": evaluation_id or f"eval-{uuid.uuid4().hex[:10]}",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "query": clean_query,
        "category": sanitize_text(category) or "General",
        "reviewer_name": sanitize_text(reviewer_name) or "Analyst",
        "session_notes": sanitize_text(session_notes),
        "is_synthetic": bool(is_synthetic),
        "weights": norm_weights,
        "duplicate_warnings": [
            {"first_index": i, "duplicate_index": j, "reason": msg}
            for i, j, msg in duplicates
        ],
        "results": evaluated_results,
        "claims": claim_list,
        "fact_summary": global_fact_summary,
        "summary_metrics": {
            "total_results": len(evaluated_results),
            "avg_relevance_score": avg_relevance,
            "avg_content_quality_score": avg_quality,
            "avg_overall_score": avg_overall,
            "top_result_title": ranked[0]["title"] if ranked else "",
            "top_result_score": ranked[0]["overall"]["final_display_score"] if ranked else 0.0,
        },
    }
