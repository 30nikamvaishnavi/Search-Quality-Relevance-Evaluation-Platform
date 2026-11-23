"""Page 5: About SearchEval Methodology, Transparency, and Limitations."""

from __future__ import annotations

import streamlit as st

from src.utils.ui import configure_page, render_disclaimer, render_sidebar_info

configure_page("About Project", icon="ℹ️")
render_sidebar_info()

st.title("About SearchEval")
st.caption("Search Quality & Relevance Evaluation Platform — Methodology & Transparency Guide")
render_disclaimer()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Project Objective")
    st.write(
        "SearchEval simulates the analytical workflow of a Search Quality Analyst or Personalized "
        "Internet Assessor. It provides structured, transparent heuristics and evidence-tracking "
        "workflows so human reviewers can evaluate search results systematically."
    )

    st.subheader("Evaluation Dimensions")
    st.markdown(
        """
        - **Search Relevance (Default 30%)**: Uses Scikit-learn TF-IDF vectorization (unigrams and bigrams)
          and cosine similarity across query-title and query-description pairs, combined with meaningful keyword overlap.
        - **Content Quality (Default 20%)**: Assesses completeness, Flesch-based readability, non-stuffed
          keyword relevance, explanatory usefulness, and repetitive/clickbait content detection.
        - **Source Credibility (Default 20%)**: Evaluates HTTPS transport, identifiable publisher, author
          attribution, publication date currency, and supporting references. Domain suffixes (`.gov`, `.edu`)
          are never assumed automatically trustworthy.
        - **Factual Evidence Assessment (Default 20%)**: Driven strictly by human-reviewed claims backed by
          evidence text and source URLs (`Supported`, `Contradicted`, `Unverified`).
        - **User Intent Alignment (Default 10%)**: Transparent rule-based classification (`informational`,
          `navigational`, `transactional`, `timely`) matched against snippet and metadata signals.
        """
    )

with col2:
    st.subheader("Key Safeguards & Design Principles")
    st.markdown(
        """
        1. **No Automated Truth Claims**: Cosine similarity measures lexical match, not factual accuracy.
        2. **Insufficient-Evidence Warnings**: When factual claims are absent or lack verifiable evidence,
           SearchEval warns the reviewer and sets factual evidence contribution to `0` rather than pretending accuracy is verified.
        3. **Automated vs. Human Separation**: Automated heuristic scores and manual reviewer overrides/labels
           (`Relevant`, `Partially Relevant`, `Irrelevant`) are stored and displayed separately.
        4. **Local-First & Zero Paid APIs**: Runs 100% locally with Python, Streamlit, Scikit-learn, Pandas,
           NumPy, Plotly, and JSON persistence.
        """
    )

    st.subheader("Limitations")
    st.markdown(
        """
        - Snippet-level text analysis cannot inspect full external web pages without fetching live URLs.
        - Lexical TF-IDF similarity does not capture deep semantic synonyms outside shared vocabulary.
        - All included starter scenarios use synthetic `.invalid` / `example.*` URLs for demonstration.
        """
    )
