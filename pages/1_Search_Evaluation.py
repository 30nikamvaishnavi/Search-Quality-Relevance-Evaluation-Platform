"""Page 1: New Search Evaluation with configurable weights, automated signals, and manual judgment."""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

from src.data.sample_data import SYNTHETIC_SAMPLE_NOTICE, get_sample_scenarios, get_scenario_by_id
from src.data.storage import save_evaluation
from src.evaluator.pipeline import evaluate_search_session
from src.evaluator.scoring import DEFAULT_WEIGHTS, RELEVANCE_LABELS, normalize_weights
from src.utils.exporters import export_evaluation_json, export_results_csv
from src.utils.ui import configure_page, render_disclaimer, render_sidebar_info
from src.utils.validators import (
    detect_duplicate_results,
    sanitize_text,
    validate_query,
    validate_search_result,
)

configure_page("New Search Evaluation", icon="📝")
render_sidebar_info()

st.title("New Search Evaluation")
st.caption("Evaluate search engine results using transparent NLP heuristics paired with human reviewer judgment.")
render_disclaimer()

# Initialize session state for builder results and active evaluation
if "draft_query" not in st.session_state:
    st.session_state.draft_query = ""
if "draft_category" not in st.session_state:
    st.session_state.draft_category = "Technology"
if "draft_results" not in st.session_state:
    st.session_state.draft_results = [
        {
            "result_id": f"res-{uuid.uuid4().hex[:6]}",
            "title": "",
            "url": "",
            "description": "",
            "source_name": "",
            "author": "",
            "published_date": "",
            "supporting_evidence": "",
        }
    ]
if "draft_claims" not in st.session_state:
    st.session_state.draft_claims = []
if "draft_is_synthetic" not in st.session_state:
    st.session_state.draft_is_synthetic = False

# Sample loader bar
scenarios = get_sample_scenarios()
scenario_map = {f"[{s['category']}] {s['query']}": s["id"] for s in scenarios}
with st.expander("Load a Synthetic Sample Query (12 Scenarios Across 5 Domains)", expanded=False):
    st.info(SYNTHETIC_SAMPLE_NOTICE)
    sample_choice = st.selectbox("Choose sample scenario", options=list(scenario_map.keys()))
    if st.button("Load Selected Sample Into Form", type="secondary"):
        chosen = get_scenario_by_id(scenario_map[sample_choice])
        if chosen:
            st.session_state.draft_query = chosen["query"]
            st.session_state.draft_category = chosen["category"]
            st.session_state.draft_results = [
                {
                    "result_id": f"res-{uuid.uuid4().hex[:6]}",
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                    "source_name": r.get("source_name", ""),
                    "author": r.get("author", ""),
                    "published_date": r.get("published_date", ""),
                    "supporting_evidence": r.get("supporting_evidence", ""),
                    "reference_urls": r.get("reference_urls", []),
                }
                for r in chosen["results"]
            ]
            st.session_state.draft_claims = list(chosen.get("claims", []))
            st.session_state.draft_is_synthetic = True
            st.success(f"Loaded sample scenario: {chosen['query']}")
            st.rerun()

# Sidebar scoring weight configuration
with st.sidebar:
    st.markdown("### Scoring Weights")
    st.caption("Adjust raw weights; they are automatically normalized to 100%.")
    w_rel = st.slider("Search Relevance", 0, 100, int(DEFAULT_WEIGHTS["search_relevance"] * 100))
    w_qual = st.slider("Content Quality", 0, 100, int(DEFAULT_WEIGHTS["content_quality"] * 100))
    w_cred = st.slider("Source Credibility", 0, 100, int(DEFAULT_WEIGHTS["source_credibility"] * 100))
    w_fact = st.slider("Factual Evidence", 0, 100, int(DEFAULT_WEIGHTS["factual_evidence"] * 100))
    w_intent = st.slider("User Intent Alignment", 0, 100, int(DEFAULT_WEIGHTS["intent_alignment"] * 100))

    raw_weights = {
        "search_relevance": float(w_rel),
        "content_quality": float(w_qual),
        "source_credibility": float(w_cred),
        "factual_evidence": float(w_fact),
        "intent_alignment": float(w_intent),
    }
    try:
        normalized_weights = normalize_weights(raw_weights)
        st.caption(
            "Normalized: "
            + " · ".join(f"{k.replace('_', ' ').title()}: {v * 100:.1f}%" for k, v in normalized_weights.items())
        )
    except ValueError as err:
        st.error(str(err))
        normalized_weights = DEFAULT_WEIGHTS

# Query and session metadata
col_q, col_cat, col_rev = st.columns([2.2, 1.0, 1.0])
with col_q:
    query_input = st.text_input(
        "Search Query *",
        value=st.session_state.draft_query,
        placeholder="e.g., how do python list comprehensions work with conditions",
    )
    st.session_state.draft_query = query_input
with col_cat:
    categories = [
        "Educational Information",
        "Technology",
        "Health Information",
        "Government Information",
        "News & Current Events",
        "General",
    ]
    cat_idx = categories.index(st.session_state.draft_category) if st.session_state.draft_category in categories else 0
    category_input = st.selectbox("Topic Category", options=categories, index=cat_idx)
    st.session_state.draft_category = category_input
with col_rev:
    reviewer_input = st.text_input("Reviewer Name", value="Search Quality Analyst")

session_notes_input = st.text_area(
    "Session Assessment Notes (Optional)",
    placeholder="Document search intent expectations or overall observations...",
    height=68,
)

# Search Results Builder
st.subheader("Search Results to Evaluate")
btn_col1, btn_col2, _ = st.columns([1, 1, 3])
with btn_col1:
    if st.button("+ Add Another Search Result", use_container_width=True):
        st.session_state.draft_results.append(
            {
                "result_id": f"res-{uuid.uuid4().hex[:6]}",
                "title": "",
                "url": "",
                "description": "",
                "source_name": "",
                "author": "",
                "published_date": "",
                "supporting_evidence": "",
            }
        )
        st.rerun()
with btn_col2:
    if st.button("Reset Form", use_container_width=True):
        st.session_state.draft_query = ""
        st.session_state.draft_results = [
            {
                "result_id": f"res-{uuid.uuid4().hex[:6]}",
                "title": "",
                "url": "",
                "description": "",
                "source_name": "",
                "author": "",
                "published_date": "",
                "supporting_evidence": "",
            }
        ]
        st.session_state.draft_claims = []
        st.session_state.draft_is_synthetic = False
        st.session_state.pop("active_evaluation", None)
        st.rerun()

for idx, res in enumerate(st.session_state.draft_results):
    with st.expander(f"Result #{idx + 1}: {res.get('title') or 'Untitled Result'}", expanded=True):
        r1, r2 = st.columns([1.3, 1.2])
        with r1:
            res["title"] = st.text_input("Title *", value=res.get("title", ""), key=f"title_{idx}")
            res["url"] = st.text_input("URL *", value=res.get("url", ""), placeholder="https://example.org/page", key=f"url_{idx}")
            res["source_name"] = st.text_input("Source Name *", value=res.get("source_name", ""), key=f"src_{idx}")
        with r2:
            res["author"] = st.text_input("Author (Optional)", value=res.get("author", ""), key=f"auth_{idx}")
            res["published_date"] = st.text_input(
                "Published Date (Optional, YYYY-MM-DD)",
                value=res.get("published_date", ""),
                placeholder="2026-01-15",
                key=f"date_{idx}",
            )
            res["supporting_evidence"] = st.text_input(
                "Supporting Evidence Summary (Optional)",
                value=res.get("supporting_evidence", ""),
                key=f"evid_{idx}",
            )
        res["description"] = st.text_area(
            "Description / Snippet *",
            value=res.get("description", ""),
            height=80,
            key=f"desc_{idx}",
        )
        if len(st.session_state.draft_results) > 1 and st.button(f"Remove Result #{idx + 1}", key=f"rm_{idx}"):
            st.session_state.draft_results.pop(idx)
            st.rerun()

if st.button("Run Search Quality Evaluation", type="primary", use_container_width=True):
    q_ok, q_msg = validate_query(query_input)
    if not q_ok:
        st.error(q_msg)
    elif not st.session_state.draft_results:
        st.error("Please add at least one search result to evaluate.")
    else:
        all_errors: list[str] = []
        for idx, res in enumerate(st.session_state.draft_results):
            ok, errs = validate_search_result(res)
            if not ok:
                for err in errs:
                    all_errors.append(f"Result #{idx + 1}: {err}")

        if all_errors:
            for err in all_errors:
                st.error(err)
        else:
            dups = detect_duplicate_results(st.session_state.draft_results)
            if dups:
                for first_i, dup_i, reason in dups:
                    st.warning(f"Duplicate detected between Result #{first_i + 1} and Result #{dup_i + 1}: {reason}")

            eval_record = evaluate_search_session(
                query=query_input,
                results=st.session_state.draft_results,
                claims=st.session_state.draft_claims,
                weights=normalized_weights,
                category=category_input,
                reviewer_name=reviewer_input,
                session_notes=session_notes_input,
                is_synthetic=st.session_state.draft_is_synthetic,
            )
            st.session_state.active_evaluation = eval_record
            st.success("Automated evaluation complete. Review signals below and apply human judgments before saving.")

# Display evaluation results & manual reviewer override controls
active_eval: dict[str, Any] | None = st.session_state.get("active_evaluation")
if active_eval:
    st.divider()
    st.subheader("Evaluation Results: Automated Signals vs. Human Judgment")

    if active_eval["fact_summary"]["insufficient_evidence_warning"]:
        st.warning(active_eval["fact_summary"]["insufficient_evidence_warning"])

    review_updates: dict[str, dict[str, Any]] = {}
    for idx, res in enumerate(active_eval.get("results", [])):
        rel = res["relevance"]
        qual = res["content_quality"]
        cred = res["credibility"]
        overall = res["overall"]

        with st.container(border=True):
            header_c1, header_c2 = st.columns([3, 1])
            with header_c1:
                st.markdown(f"### #{idx + 1}. {res['title']}")
                st.caption(f"Source: {res['source_name']} · URL: {res['url']} · Domain Type: {cred['domain_type']}")
            with header_c2:
                st.metric("Overall Score", f"{overall['final_display_score']}/100", delta=overall["score_source"])

            st.markdown('<span class="se-badge-auto">AUTOMATED SIGNALS (DO NOT ESTABLISH FACTUAL TRUTH)</span>', unsafe_allow_html=True)
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Relevance", f"{rel['overall_relevance_score']}/100")
            m2.metric("Title Sim", f"{rel['query_title_similarity']}/100")
            m3.metric("Snippet Sim", f"{rel['query_description_similarity']}/100")
            m4.metric("Content Quality", f"{qual['overall_quality_score']}/100")
            m5.metric("Credibility", f"{cred['final_credibility_score']}/100")

            detail_c1, detail_c2, detail_c3 = st.columns(3)
            with detail_c1:
                st.markdown("**Relevance & Intent**")
                st.write(f"Detected Intent: `{rel['detected_intent']}` ({rel['intent_alignment_score']}/100)")
                st.write(f"Matched Terms: {', '.join(rel['matched_keywords']) or 'None'}")
                st.write(f"Missing Terms: {', '.join(rel['missing_keywords']) or 'None'}")
                for rsn in rel["intent_reasons"]:
                    st.caption(f"• {rsn}")
            with detail_c2:
                st.markdown("**Content Quality Breakdown**")
                st.write(
                    f"Completeness: {qual['completeness_score']} · Readability: {qual['readability_score']} · "
                    f"Usefulness: {qual['usefulness_score']} · Uniqueness: {qual['uniqueness_score']}"
                )
                for exp in qual["explanations"]:
                    st.caption(f"• {exp}")
                for wrn in qual["warnings"]:
                    st.caption(f"⚠️ {wrn}")
            with detail_c3:
                st.markdown("**Source Credibility Signals**")
                for sig in cred["signals"]:
                    st.caption(f"✓ {sig}")
                for caut in cred["cautions"]:
                    st.caption(f"⚠️ {caut}")

            st.markdown('<span class="se-badge-human">HUMAN REVIEWER JUDGMENT</span>', unsafe_allow_html=True)
            h1, h2, h3 = st.columns([1, 1, 1.4])
            with h1:
                lbl_options = ["Unlabeled", *RELEVANCE_LABELS]
                current_lbl = overall.get("human_label") or "Unlabeled"
                chosen_lbl = st.selectbox(
                    "Relevance Judgment",
                    options=lbl_options,
                    index=lbl_options.index(current_lbl) if current_lbl in lbl_options else 0,
                    key=f"hlbl_{res['result_id']}",
                )
            with h2:
                use_override = st.checkbox(
                    "Apply Manual Score Override",
                    value=overall.get("human_score_override") is not None,
                    key=f"hov_chk_{res['result_id']}",
                )
                override_val = st.number_input(
                    "Manual Score (0-100)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(overall.get("human_score_override") or overall["automated_score"]),
                    step=1.0,
                    disabled=not use_override,
                    key=f"hov_val_{res['result_id']}",
                )
                cred_adj = st.slider(
                    "Credibility Adjustment (-40 to +40)",
                    min_value=-40,
                    max_value=40,
                    value=int(cred.get("manual_adjustment", 0)),
                    key=f"cadj_{res['result_id']}",
                )
            with h3:
                comments = st.text_area(
                    "Reviewer Comments & Credibility Rationale",
                    value=overall.get("human_comments", ""),
                    height=105,
                    key=f"hcom_{res['result_id']}",
                )

            review_updates[res["result_id"]] = {
                "human_label": None if chosen_lbl == "Unlabeled" else chosen_lbl,
                "human_score_override": float(override_val) if use_override else None,
                "human_comments": sanitize_text(comments),
                "cred_adj": float(cred_adj),
            }

    act1, act2, act3 = st.columns(3)
    with act1:
        if st.button("Apply Judgments & Save Evaluation", type="primary", use_container_width=True):
            # Re-run with manual credibility adjustments and human labels applied cleanly
            updated_inputs = []
            for idx, orig in enumerate(st.session_state.draft_results):
                res_obj = active_eval["results"][idx]
                upd = review_updates.get(res_obj["result_id"], {})
                merged = dict(orig)
                merged["result_id"] = res_obj["result_id"]
                merged["human_label"] = upd.get("human_label")
                merged["human_score_override"] = upd.get("human_score_override")
                merged["human_comments"] = upd.get("human_comments", "")
                merged["manual_credibility_adjustment"] = upd.get("cred_adj", 0.0)
                merged["credibility_explanation"] = upd.get("human_comments", "")
                updated_inputs.append(merged)

            final_record = evaluate_search_session(
                query=active_eval["query"],
                results=updated_inputs,
                claims=active_eval.get("claims", []),
                weights=active_eval.get("weights"),
                category=active_eval.get("category", "General"),
                reviewer_name=active_eval.get("reviewer_name", "Analyst"),
                session_notes=session_notes_input or active_eval.get("session_notes", ""),
                is_synthetic=active_eval.get("is_synthetic", False),
                evaluation_id=active_eval["evaluation_id"],
            )
            st.session_state.active_evaluation = final_record
            saved_id = save_evaluation(final_record)
            st.success(f"Saved evaluation `{saved_id}` to local history.")

    with act2:
        st.download_button(
            label="Export Result Assessments (CSV)",
            data=export_results_csv(active_eval),
            file_name=f"{active_eval['evaluation_id']}_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with act3:
        st.download_button(
            label="Export Detailed Report (JSON)",
            data=export_evaluation_json(active_eval),
            file_name=f"{active_eval['evaluation_id']}.json",
            mime="application/json",
            use_container_width=True,
        )
