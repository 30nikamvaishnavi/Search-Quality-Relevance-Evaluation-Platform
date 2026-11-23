"""Page 4: Local Evaluation History, Search, Review Editing, Deletion, and Exports."""

from __future__ import annotations

import streamlit as st

from src.data.storage import (
    delete_evaluation,
    load_evaluations,
    search_evaluations,
    update_evaluation_review,
)
from src.evaluator.scoring import RELEVANCE_LABELS
from src.utils.exporters import (
    export_all_evaluations_json,
    export_evaluation_json,
    export_results_csv,
    export_summary_csv,
)
from src.utils.ui import (
    configure_page,
    ensure_sample_history_seeded,
    render_disclaimer,
    render_sidebar_info,
)

configure_page("Evaluation History", icon="🗂️")
render_sidebar_info()

st.title("Evaluation History")
st.caption("Search, inspect, update manual reviews, delete records, and export historical reports.")
render_disclaimer()

ensure_sample_history_seeded()
all_records = load_evaluations()

categories = sorted({r.get("category", "General") for r in all_records})
f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    search_term = st.text_input("Search by query or reviewer notes", placeholder="Type keywords...")
with f2:
    cat_filter = st.selectbox("Filter by Category", options=["All", *categories])
with f3:
    lbl_filter = st.selectbox("Filter by Human Label", options=["All", *RELEVANCE_LABELS])

filtered = search_evaluations(
    query_text=search_term,
    category=cat_filter,
    label_filter=lbl_filter,
)

st.write(f"Showing **{len(filtered)}** of **{len(all_records)}** stored evaluation record(s).")

if filtered:
    top_exp1, top_exp2 = st.columns(2)
    with top_exp1:
        st.download_button(
            "Download Filtered Summary (CSV)",
            data=export_summary_csv(filtered),
            file_name="searcheval_filtered_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with top_exp2:
        st.download_button(
            "Download Filtered Archive (JSON)",
            data=export_all_evaluations_json(filtered),
            file_name="searcheval_filtered_archive.json",
            mime="application/json",
            use_container_width=True,
        )

for rec in filtered:
    eval_id = rec["evaluation_id"]
    metrics = rec.get("summary_metrics", {})
    synth_tag = " [Synthetic]" if rec.get("is_synthetic") else ""
    header = (
        f"{rec['query']}{synth_tag} — Avg Score: {metrics.get('avg_overall_score', 0.0)}/100 "
        f"({metrics.get('total_results', 0)} results · {rec.get('created_at', '')})"
    )
    with st.expander(header, expanded=False):
        st.write(
            f"**Evaluation ID:** `{eval_id}` · **Category:** {rec.get('category', 'General')} · "
            f"**Reviewer:** {rec.get('reviewer_name', 'Analyst')}"
        )
        if rec.get("session_notes"):
            st.info(f"Session Notes: {rec['session_notes']}")

        review_edits: dict[str, dict] = {}
        for res in rec.get("results", []):
            overall = res.get("overall", {})
            st.markdown(f"**{res['title']}** (`{res['url']}`)")
            c1, c2, c3 = st.columns([1.2, 1, 1.5])
            with c1:
                st.caption(
                    f"Automated: {overall.get('automated_score', 0)}/100 · "
                    f"Current Display: {overall.get('final_display_score', 0)}/100 ({overall.get('score_source', '')})"
                )
                lbl_opts = ["Unlabeled", *RELEVANCE_LABELS]
                cur_lbl = overall.get("human_label") or "Unlabeled"
                new_lbl = st.selectbox(
                    "Human Label",
                    options=lbl_opts,
                    index=lbl_opts.index(cur_lbl) if cur_lbl in lbl_opts else 0,
                    key=f"hist_lbl_{eval_id}_{res['result_id']}",
                )
            with c2:
                use_ov = st.checkbox(
                    "Override Score",
                    value=overall.get("human_score_override") is not None,
                    key=f"hist_ovchk_{eval_id}_{res['result_id']}",
                )
                ov_score = st.number_input(
                    "Manual Score",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(overall.get("human_score_override") or overall.get("automated_score", 0.0)),
                    disabled=not use_ov,
                    key=f"hist_ovval_{eval_id}_{res['result_id']}",
                )
            with c3:
                new_com = st.text_input(
                    "Reviewer Comment",
                    value=overall.get("human_comments", ""),
                    key=f"hist_com_{eval_id}_{res['result_id']}",
                )

            review_edits[res["result_id"]] = {
                "human_label": None if new_lbl == "Unlabeled" else new_lbl,
                "human_score_override": float(ov_score) if use_ov else None,
                "human_comments": new_com,
            }

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("Save Review Updates", key=f"save_upd_{eval_id}", type="primary", use_container_width=True) and update_evaluation_review(eval_id, review_edits):
                st.success("Review updates saved.")
                st.rerun()
        with b2:
            st.download_button(
                "Results CSV",
                data=export_results_csv(rec),
                file_name=f"{eval_id}_results.csv",
                mime="text/csv",
                key=f"dl_csv_{eval_id}",
                use_container_width=True,
            )
        with b3:
            st.download_button(
                "Detailed JSON",
                data=export_evaluation_json(rec),
                file_name=f"{eval_id}.json",
                mime="application/json",
                key=f"dl_json_{eval_id}",
                use_container_width=True,
            )
        with b4:
            if st.button("Delete Record", key=f"del_{eval_id}", use_container_width=True) and delete_evaluation(eval_id):
                st.success(f"Deleted `{eval_id}`.")
                st.rerun()
