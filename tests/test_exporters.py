"""Unit tests for CSV/JSON exporters, input validators, and synthetic sample scenarios."""

from __future__ import annotations

import json

from src.data.sample_data import build_sample_evaluations, get_sample_scenarios
from src.evaluator.pipeline import evaluate_search_session
from src.utils.exporters import (
    export_all_evaluations_json,
    export_evaluation_json,
    export_results_csv,
    export_summary_csv,
)
from src.utils.validators import detect_duplicate_results, validate_query, validate_url


def test_csv_and_json_exports_and_formula_safety() -> None:
    """Exports produce valid CSV/JSON and neutralize spreadsheet formula prefixes."""
    rec = evaluate_search_session(
        query="=SUM(1,2) formula query",
        results=[
            {
                "title": "Test Title",
                "url": "https://example.org/test",
                "description": "Valid snippet describing test query concepts.",
                "source_name": "Example Org",
            }
        ],
        evaluation_id="eval-exp-1",
    )

    summary_csv = export_summary_csv([rec])
    results_csv = export_results_csv(rec)
    single_json = export_evaluation_json(rec)
    all_json = export_all_evaluations_json([rec])

    assert "'=SUM(1,2) formula query" in summary_csv
    assert "eval-exp-1" in results_csv
    assert json.loads(single_json)["evaluation_id"] == "eval-exp-1"
    assert len(json.loads(all_json)) == 1


def test_validators_and_duplicate_detection() -> None:
    """URL, query validation, and duplicate result detection catch invalid inputs."""
    assert validate_query("")[0] is False
    assert validate_url("javascript:alert(1)")[0] is False
    assert validate_url("https://example.org/path")[0] is True

    dups = detect_duplicate_results(
        [
            {"title": "A", "url": "https://example.org/page/", "source_name": "S"},
            {"title": "B", "url": "https://example.org/page", "source_name": "S2"},
        ]
    )
    assert len(dups) == 1


def test_sample_dataset_coverage() -> None:
    """At least 10 synthetic sample scenarios exist across required domains."""
    scenarios = get_sample_scenarios()
    assert len(scenarios) >= 10
    categories = {s["category"] for s in scenarios}
    assert {
        "Educational Information",
        "Technology",
        "Health Information",
        "Government Information",
        "News & Current Events",
    }.issubset(categories)

    built = build_sample_evaluations(limit=4)
    assert len(built) == 4
    assert all(item["is_synthetic"] is True for item in built)
