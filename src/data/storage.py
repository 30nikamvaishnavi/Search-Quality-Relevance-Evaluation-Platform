"""Safe local JSON persistence for SearchEval evaluation records."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.utils.validators import sanitize_text

DEFAULT_STORAGE_PATH = Path(os.getenv("SEARCHEVAL_DATA_PATH", "data/evaluations.json"))


def _resolve_path(filepath: Path | str | None) -> Path:
    """Resolve storage path and ensure its parent directory exists."""
    target = Path(filepath) if filepath is not None else DEFAULT_STORAGE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _atomic_write_json(target: Path, payload: list[dict[str, Any]]) -> None:
    """Safely write JSON data atomically using a temporary file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".eval_", suffix=".json", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def load_evaluations(filepath: Path | str | None = None) -> list[dict[str, Any]]:
    """Load all saved evaluation records from local JSON storage."""
    target = _resolve_path(filepath)
    if not target.exists():
        return []
    raw_text = target.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Evaluation storage file '{target}' contains invalid JSON.") from exc
    if not isinstance(data, list):
        raise ValueError(f"Evaluation storage file '{target}' must contain a JSON list.")
    return [item for item in data if isinstance(item, dict)]


def save_evaluation(record: dict[str, Any], filepath: Path | str | None = None) -> str:
    """Save or update an evaluation record in local JSON storage and return its ID."""
    if not isinstance(record, dict) or not record.get("evaluation_id"):
        raise ValueError("Evaluation record must be a dictionary with an 'evaluation_id'.")

    target = _resolve_path(filepath)
    records = load_evaluations(target)
    eval_id = str(record["evaluation_id"])

    updated = False
    for idx, existing in enumerate(records):
        if existing.get("evaluation_id") == eval_id:
            records[idx] = record
            updated = True
            break
    if not updated:
        records.insert(0, record)

    _atomic_write_json(target, records)
    return eval_id


def get_evaluation(eval_id: str, filepath: Path | str | None = None) -> dict[str, Any] | None:
    """Retrieve a single evaluation record by ID."""
    records = load_evaluations(filepath)
    for item in records:
        if item.get("evaluation_id") == eval_id:
            return item
    return None


def delete_evaluation(eval_id: str, filepath: Path | str | None = None) -> bool:
    """Delete an evaluation record by ID. Returns True if deleted."""
    target = _resolve_path(filepath)
    records = load_evaluations(target)
    filtered = [item for item in records if item.get("evaluation_id") != eval_id]
    if len(filtered) == len(records):
        return False
    _atomic_write_json(target, filtered)
    return True


def search_evaluations(
    query_text: str = "",
    category: str | None = None,
    label_filter: str | None = None,
    filepath: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Filter saved evaluations by query substring, category, or human relevance label."""
    records = load_evaluations(filepath)
    needle = sanitize_text(query_text).lower()
    cat_filter = sanitize_text(category).lower() if category and category != "All" else ""
    lbl_filter = sanitize_text(label_filter).lower() if label_filter and label_filter != "All" else ""

    matched: list[dict[str, Any]] = []
    for item in records:
        item_query = sanitize_text(item.get("query")).lower()
        item_notes = sanitize_text(item.get("session_notes")).lower()
        item_cat = sanitize_text(item.get("category")).lower()

        if needle and needle not in item_query and needle not in item_notes:
            continue
        if cat_filter and item_cat != cat_filter:
            continue
        if lbl_filter:
            result_labels = [
                sanitize_text(res.get("overall", {}).get("human_label")).lower()
                for res in item.get("results", [])
            ]
            if lbl_filter not in result_labels:
                continue
        matched.append(item)

    return matched


def update_evaluation_review(
    eval_id: str,
    result_updates: dict[str, dict[str, Any]],
    session_notes: str | None = None,
    filepath: Path | str | None = None,
) -> bool:
    """Update human reviewer judgments on an existing saved evaluation."""
    target = _resolve_path(filepath)
    records = load_evaluations(target)
    found = False

    for rec in records:
        if rec.get("evaluation_id") != eval_id:
            continue
        found = True
        if session_notes is not None:
            rec["session_notes"] = sanitize_text(session_notes)
        rec["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds")

        for res in rec.get("results", []):
            rid = res.get("result_id")
            if rid in result_updates:
                upd = result_updates[rid]
                overall = res.get("overall", {})
                if "human_label" in upd:
                    overall["human_label"] = upd["human_label"]
                if "human_score_override" in upd:
                    override = upd["human_score_override"]
                    overall["human_score_override"] = override
                    if override is not None:
                        overall["final_display_score"] = round(float(override), 2)
                        overall["score_source"] = "Human Reviewer Override"
                    else:
                        overall["final_display_score"] = overall.get("automated_score", 0.0)
                        overall["score_source"] = "Automated Heuristic"
                if "human_comments" in upd:
                    overall["human_comments"] = sanitize_text(upd["human_comments"])
                res["overall"] = overall

        results = rec.get("results", [])
        if results:
            ranked = sorted(
                results,
                key=lambda r: r.get("overall", {}).get("final_display_score", 0.0),
                reverse=True,
            )
            rec["summary_metrics"]["avg_overall_score"] = round(
                sum(r.get("overall", {}).get("final_display_score", 0.0) for r in results)
                / len(results),
                2,
            )
            rec["summary_metrics"]["top_result_title"] = ranked[0].get("title", "")
            rec["summary_metrics"]["top_result_score"] = ranked[0].get("overall", {}).get(
                "final_display_score", 0.0
            )
        break

    if not found:
        return False

    _atomic_write_json(target, records)
    return True
