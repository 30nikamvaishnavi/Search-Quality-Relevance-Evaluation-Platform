"""Unit tests for local evaluation history storage CRUD and search."""

from __future__ import annotations

from pathlib import Path

from src.data.storage import (
    delete_evaluation,
    get_evaluation,
    load_evaluations,
    save_evaluation,
    search_evaluations,
    update_evaluation_review,
)
from src.evaluator.pipeline import evaluate_search_session


def test_storage_save_load_search_update_delete(tmp_path: Path) -> None:
    """Full lifecycle of saving, querying, updating human review, and deleting evaluations."""
    db_file = tmp_path / "evaluations.json"

    rec = evaluate_search_session(
        query="python list comprehensions",
        results=[
            {
                "title": "Python List Comprehensions Guide",
                "url": "https://example.edu/python-lists",
                "description": "Explains list comprehensions with conditional filtering examples.",
                "source_name": "Example Edu",
            }
        ],
        category="Educational Information",
        evaluation_id="eval-test-001",
    )
    save_evaluation(rec, filepath=db_file)

    loaded = load_evaluations(filepath=db_file)
    assert len(loaded) == 1
    assert get_evaluation("eval-test-001", filepath=db_file) is not None

    # Update human judgment
    rid = loaded[0]["results"][0]["result_id"]
    updated_ok = update_evaluation_review(
        "eval-test-001",
        result_updates={
            rid: {
                "human_label": "Relevant",
                "human_score_override": 88.0,
                "human_comments": "Clear beginner guide.",
            }
        },
        filepath=db_file,
    )
    assert updated_ok is True

    # Search by query and human label
    found = search_evaluations(query_text="comprehensions", label_filter="Relevant", filepath=db_file)
    assert len(found) == 1
    assert found[0]["results"][0]["overall"]["final_display_score"] == 88.0

    # Delete
    assert delete_evaluation("eval-test-001", filepath=db_file) is True
    assert load_evaluations(filepath=db_file) == []
    assert delete_evaluation("non-existent", filepath=db_file) is False
