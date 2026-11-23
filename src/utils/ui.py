"""Shared Streamlit UI styling, header components, and state helpers for SearchEval."""

from __future__ import annotations

import streamlit as st

from src.data.sample_data import build_sample_evaluations
from src.data.storage import load_evaluations, save_evaluation

APP_DISCLAIMER = (
    "SearchEval is an independent evaluation-support tool simulating a Search Quality Analyst "
    "workflow. It is NOT an official Google or TELUS rating system, and automated similarity or "
    "heuristic scores never establish factual truth."
)


def configure_page(title: str, icon: str = "🔎") -> None:
    """Apply consistent page configuration and clean editorial styling."""
    st.set_page_config(
        page_title=f"{title} | SearchEval",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1280px;
        }
        .se-banner {
            background: linear-gradient(135deg, #0F4C81 0%, #1E3A5F 100%);
            color: #FFFFFF;
            padding: 1.25rem 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .se-banner h1 {
            color: #FFFFFF;
            margin: 0 0 0.35rem 0;
            font-size: 1.65rem;
            font-weight: 700;
        }
        .se-banner p {
            color: #E2E8F0;
            margin: 0;
            font-size: 0.94rem;
        }
        .se-disclaimer {
            background-color: #FEF3C7;
            border-left: 4px solid #D97706;
            color: #78350F;
            padding: 0.75rem 1rem;
            border-radius: 6px;
            font-size: 0.88rem;
            margin-bottom: 1.15rem;
        }
        .se-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.85rem;
        }
        .se-badge-auto {
            display: inline-block;
            background-color: #DBEAFE;
            color: #1E40AF;
            padding: 0.15rem 0.55rem;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .se-badge-human {
            display: inline-block;
            background-color: #DCFCE7;
            color: #166534;
            padding: 0.15rem 0.55rem;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .se-badge-warn {
            display: inline-block;
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 0.15rem 0.55rem;
            border-radius: 4px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_info() -> None:
    """Render shared sidebar metadata and clear scope reminder."""
    with st.sidebar:
        st.markdown("### SearchEval")
        st.caption("Search Quality & Relevance Evaluation Platform")
        st.divider()
        st.info(
            "Local-first workflow: no API keys required. Automated scores assist human "
            "reviewers and are kept distinct from manual judgments."
        )


def render_disclaimer() -> None:
    """Display non-official evaluation disclaimer banner."""
    st.markdown(
        f'<div class="se-disclaimer"><strong>Evaluation Scope Notice:</strong> {APP_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


def ensure_sample_history_seeded() -> list[dict]:
    """Load saved evaluations; if none exist yet, seed 4 synthetic starter evaluations."""
    records = load_evaluations()
    if not records:
        for sample_rec in build_sample_evaluations(limit=4):
            save_evaluation(sample_rec)
        records = load_evaluations()
    return records


def score_color(score: float) -> str:
    """Return hex color associated with a 0-100 evaluation score."""
    if score >= 75:
        return "#15803D"
    if score >= 50:
        return "#B45309"
    return "#B91C1C"
