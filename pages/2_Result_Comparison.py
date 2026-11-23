"""Page 2: Side-by-Side Search Result Comparison."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.storage import load_evaluations
from src.utils.exporters import export_evaluation_json, export_results_csv
from src.utils.ui import (
    configure_page,
    ensure_sample_history_seeded,
    render_disclaimer,
    render_sidebar_info,
)

configure_page("Result Comparison", icon="⚖️")
render_sidebar_info()

st.title("Search Result Comparison")
st.caption("Compare multiple search results across relevance, intent alignment, content quality, and source credibility.")
render_disclaimer()

records = ensure_sample_history_seeded()
active_eval = st.session_state.get("active_evaluation")

eval_choices: dict[str, dict] = {}
if active_eval:
    eval_choices[f"[Current Draft] {active_eval['query']} ({active_eval['evaluation_id']})"] = active_eval
for rec in load_evaluations():
    eval_choices[f"{rec['query']} ({rec.get('category', 'General')} · {rec['evaluation_id']})"] = rec

if not eval_choices:
    st.info("No evaluations available to compare yet. Create an evaluation first.")
    st.stop()

chosen_key = st.selectbox("Select Evaluation to Compare", options=list(eval_choices.keys()))
selected_eval = eval_choices[chosen_key]
results = selected_eval.get("results", [])

if not results:
    st.warning("This evaluation has no search results.")
    st.stop()

if selected_eval.get("fact_summary", {}).get("insufficient_evidence_warning"):
    st.warning(selected_eval["fact_summary"]["insufficient_evidence_warning"])

rows = []
for res in results:
    rel = res["relevance"]
    qual = res["content_quality"]
    cred = res["credibility"]
    overall = res["overall"]
    rows.append(
        {
            "Title": res["title"],
            "Source": res["source_name"],
            "Domain Type": cred["domain_type"],
            "Title Sim": rel["query_title_similarity"],
            "Snippet Sim": rel["query_description_similarity"],
            "Keyword Overlap": rel["keyword_overlap_score"],
            "Intent Alignment": rel["intent_alignment_score"],
            "Overall Relevance": rel["overall_relevance_score"],
            "Content Quality": qual["overall_quality_score"],
            "Source Credibility": cred["final_credibility_score"],
            "Automated Score": overall["automated_score"],
            "Final Score": overall["final_display_score"],
            "Score Source": overall["score_source"],
            "Human Label": overall.get("human_label") or "Unlabeled",
        }
    )

comp_df = pd.DataFrame(rows).sort_values("Final Score", ascending=False)

st.subheader("Multi-Dimensional Radar Comparison")
categories = [
    "Title Sim",
    "Snippet Sim",
    "Keyword Overlap",
    "Intent Alignment",
    "Content Quality",
    "Source Credibility",
    "Final Score",
]
fig_radar = go.Figure()
for _, row in comp_df.iterrows():
    values = [row[c] for c in categories]
    fig_radar.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=row["Title"][:45],
        )
    )
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    height=430,
    margin=dict(l=40, r=40, t=30, b=30),
)
st.plotly_chart(fig_radar, use_container_width=True)

st.subheader("Side-by-Side Score Matrix")
st.dataframe(comp_df, use_container_width=True, hide_index=True)

st.subheader("Detailed Qualitative Signals")
for res in results:
    with st.expander(f"{res['title']} — {res['overall']['final_display_score']}/100"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Matched Keywords:** " + (", ".join(res["relevance"]["matched_keywords"]) or "None"))
            st.markdown("**Missing Keywords:** " + (", ".join(res["relevance"]["missing_keywords"]) or "None"))
            st.markdown("**Quality Explanations:**")
            for exp in res["content_quality"]["explanations"]:
                st.write(f"- {exp}")
        with c2:
            st.markdown("**Credibility Signals:**")
            for sig in res["credibility"]["signals"]:
                st.write(f"- {sig}")
            st.markdown("**Cautions & Warnings:**")
            for warn in res["content_quality"]["warnings"] + res["credibility"]["cautions"]:
                st.write(f"- ⚠️ {warn}")

ex1, ex2 = st.columns(2)
with ex1:
    st.download_button(
        "Download Comparison CSV",
        data=export_results_csv(selected_eval),
        file_name=f"{selected_eval['evaluation_id']}_comparison.csv",
        mime="text/csv",
        use_container_width=True,
    )
with ex2:
    st.download_button(
        "Download Detailed JSON",
        data=export_evaluation_json(selected_eval),
        file_name=f"{selected_eval['evaluation_id']}_details.json",
        mime="application/json",
        use_container_width=True,
    )
