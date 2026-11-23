"""SearchEval – Home Dashboard (Streamlit Entry Point)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data.sample_data import SYNTHETIC_SAMPLE_NOTICE, build_sample_evaluations
from src.data.storage import load_evaluations, save_evaluation
from src.utils.exporters import export_all_evaluations_json, export_summary_csv
from src.utils.ui import (
    configure_page,
    ensure_sample_history_seeded,
    render_disclaimer,
    render_sidebar_info,
)

configure_page("Home Dashboard", icon="🔎")
render_sidebar_info()

st.markdown(
    """
    <div class="se-banner">
      <h1>SearchEval – Search Quality & Relevance Evaluation Platform</h1>
      <p>Transparent TF-IDF relevance scoring, content quality checks, source credibility signals, and human-assisted fact verification.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
render_disclaimer()

records = ensure_sample_history_seeded()

with st.sidebar:
    st.markdown("#### Quick Sample Actions")
    if st.button("Reload Starter Synthetic Samples", use_container_width=True):
        for rec in build_sample_evaluations(limit=6):
            save_evaluation(rec)
        st.success("Synthetic starter scenarios loaded into local history.")
        st.rerun()

if not records:
    st.info("No evaluations recorded yet. Open **New Search Evaluation** from the sidebar to evaluate a query.")
    st.stop()

# Flatten result-level and claim-level metrics across all stored evaluations
result_rows: list[dict] = []
supported_total = 0
contradicted_total = 0
unverified_total = 0

for eval_rec in records:
    fs = eval_rec.get("fact_summary", {})
    supported_total += int(fs.get("supported_count", 0))
    contradicted_total += int(fs.get("contradicted_count", 0))
    unverified_total += int(fs.get("unverified_count", 0))

    for res in eval_rec.get("results", []):
        rel = res.get("relevance", {})
        qual = res.get("content_quality", {})
        cred = res.get("credibility", {})
        overall = res.get("overall", {})
        result_rows.append(
            {
                "evaluation_id": eval_rec.get("evaluation_id", ""),
                "query": eval_rec.get("query", ""),
                "category": eval_rec.get("category", "General"),
                "title": res.get("title", ""),
                "source_name": res.get("source_name", ""),
                "url": res.get("url", ""),
                "relevance_score": float(rel.get("overall_relevance_score", 0.0)),
                "intent_score": float(rel.get("intent_alignment_score", 0.0)),
                "content_quality_score": float(qual.get("overall_quality_score", 0.0)),
                "credibility_score": float(cred.get("final_credibility_score", 0.0)),
                "automated_score": float(overall.get("automated_score", 0.0)),
                "final_score": float(overall.get("final_display_score", 0.0)),
                "score_source": overall.get("score_source", "Automated Heuristic"),
                "human_label": overall.get("human_label") or "Unlabeled",
                "evidence_status": overall.get("evidence_status", "Unverified"),
                "is_synthetic": eval_rec.get("is_synthetic", False),
            }
        )

df_results = pd.DataFrame(result_rows)

total_results_count = len(df_results)
avg_relevance = round(float(df_results["relevance_score"].mean()), 1) if not df_results.empty else 0.0
avg_quality = round(float(df_results["content_quality_score"].mean()), 1) if not df_results.empty else 0.0
avg_overall = round(float(df_results["final_score"].mean()), 1) if not df_results.empty else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Evaluations Saved", len(records))
col2.metric("Search Results Evaluated", total_results_count)
col3.metric("Avg Relevance Score", f"{avg_relevance}/100")
col4.metric("Avg Content Quality", f"{avg_quality}/100")
col5.metric(
    "Claims (S / C / U)",
    f"{supported_total} / {contradicted_total} / {unverified_total}",
    help="Supported / Contradicted / Unverified factual claims across evaluations.",
)

st.caption(f"Note: Starter rows labeled `(Synthetic)` come from training samples. {SYNTHETIC_SAMPLE_NOTICE}")

chart_left, chart_right = st.columns([1.15, 1.0])

with chart_left:
    st.subheader("Quality & Relevance Score Distribution")
    if not df_results.empty:
        melted = df_results.melt(
            id_vars=["title", "category"],
            value_vars=[
                "relevance_score",
                "content_quality_score",
                "credibility_score",
                "final_score",
            ],
            var_name="Dimension",
            value_name="Score",
        )
        dim_labels = {
            "relevance_score": "Relevance",
            "content_quality_score": "Content Quality",
            "credibility_score": "Source Credibility",
            "final_score": "Overall Score",
        }
        melted["Dimension"] = melted["Dimension"].map(dim_labels)
        fig_dist = px.box(
            melted,
            x="Dimension",
            y="Score",
            color="Dimension",
            points="all",
            hover_data=["title", "category"],
            color_discrete_sequence=["#0F4C81", "#0D9488", "#D97706", "#334155"],
        )
        fig_dist.update_layout(
            showlegend=False,
            yaxis_range=[0, 105],
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

with chart_right:
    st.subheader("Factual Claim Verification Breakdown")
    claim_counts = {
        "Supported": supported_total,
        "Contradicted": contradicted_total,
        "Unverified": unverified_total,
    }
    if sum(claim_counts.values()) > 0:
        fig_claims = px.bar(
            x=list(claim_counts.keys()),
            y=list(claim_counts.values()),
            color=list(claim_counts.keys()),
            color_discrete_map={
                "Supported": "#15803D",
                "Contradicted": "#B91C1C",
                "Unverified": "#D97706",
            },
            labels={"x": "Claim Status", "y": "Number of Claims"},
        )
        fig_claims.update_layout(
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
        )
        st.plotly_chart(fig_claims, use_container_width=True)
    else:
        st.info("No factual claims logged yet. Visit **Fact Verification** to review claims.")

st.subheader("Highest-Ranked Search Results Across Evaluations")
if not df_results.empty:
    top_df = df_results.sort_values("final_score", ascending=False).head(8)
    fig_top = go.Figure()
    fig_top.add_trace(
        go.Bar(
            y=top_df["title"].str.slice(0, 52),
            x=top_df["final_score"],
            name="Overall Score",
            orientation="h",
            marker_color="#0F4C81",
        )
    )
    fig_top.add_trace(
        go.Bar(
            y=top_df["title"].str.slice(0, 52),
            x=top_df["relevance_score"],
            name="Relevance Score",
            orientation="h",
            marker_color="#0D9488",
        )
    )
    fig_top.update_layout(
        barmode="group",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[0, 100], title="Score (0–100)"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_top, use_container_width=True)

    st.dataframe(
        top_df[
            [
                "query",
                "title",
                "source_name",
                "relevance_score",
                "content_quality_score",
                "credibility_score",
                "final_score",
                "score_source",
                "human_label",
                "evidence_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Compare Results Within a Saved Evaluation")
eval_options = {
    f"{r['query']} ({r.get('category', 'General')} · {r['evaluation_id']})": r
    for r in load_evaluations()
}
selected_label = st.selectbox("Select evaluation session", options=list(eval_options.keys()))
selected_eval = eval_options[selected_label]
session_results = selected_eval.get("results", [])

if session_results:
    comp_rows = [
        {
            "Title": r["title"],
            "Relevance": r["relevance"]["overall_relevance_score"],
            "Content Quality": r["content_quality"]["overall_quality_score"],
            "Credibility": r["credibility"]["final_credibility_score"],
            "Intent Alignment": r["relevance"]["intent_alignment_score"],
            "Overall Score": r["overall"]["final_display_score"],
            "Human Label": r["overall"].get("human_label") or "Unlabeled",
        }
        for r in session_results
    ]
    comp_df = pd.DataFrame(comp_rows)
    comp_melt = comp_df.melt(
        id_vars=["Title", "Human Label"],
        value_vars=["Relevance", "Content Quality", "Credibility", "Intent Alignment", "Overall Score"],
        var_name="Metric",
        value_name="Score",
    )
    fig_comp = px.bar(
        comp_melt,
        x="Metric",
        y="Score",
        color="Title",
        barmode="group",
        range_y=[0, 105],
    )
    fig_comp.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_comp, use_container_width=True)

st.subheader("Quick Dashboard Exports")
exp_col1, exp_col2 = st.columns(2)
with exp_col1:
    st.download_button(
        label="Download Evaluation Summary (CSV)",
        data=export_summary_csv(records),
        file_name="searcheval_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
with exp_col2:
    st.download_button(
        label="Download Full Evaluation Archive (JSON)",
        data=export_all_evaluations_json(records),
        file_name="searcheval_archive.json",
        mime="application/json",
        use_container_width=True,
    )
