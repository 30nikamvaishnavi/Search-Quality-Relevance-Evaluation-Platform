# SearchEval – Search Quality & Relevance Evaluation Platform

**SearchEval** is a transparent, local-first Python and Streamlit platform designed to simulate the evaluation workflow of a **Search Quality Analyst / Personalized Internet Assessor**. It helps reviewers evaluate search engine results against a user query across relevance, search intent alignment, content quality, source credibility, and evidence-backed factual claims.

> **Disclaimer:** SearchEval is an independent evaluation-support tool, **not** an official Google or TELUS rating system. Automated TF-IDF similarity and heuristic scores measure lexical and structural signals only—they never establish factual truth.

---

## Problem Statement

Evaluating search results requires balancing multiple dimensions: whether a snippet matches the user's words, whether it satisfies the underlying search intent, whether the content is readable and informative, whether the publisher provides transparent attribution, and whether factual claims are actually backed by evidence. Relying on black-box scores or assuming domain suffixes (like `.gov` or `.edu`) guarantee accuracy leads to flawed assessments. SearchEval provides an auditable, modular, and human-in-the-loop framework where automated signals assist—never replace—reviewer judgment.

---

## Key Features

- **Search Query & Multi-Result Input:** Enter queries with multiple results (title, URL, snippet, source name, optional author, publication date, supporting evidence, and reference URLs) with strict input/URL validation and duplicate detection.
- **TF-IDF Relevance & Rule-Based Intent Alignment:** Uses Scikit-learn `TfidfVectorizer` and cosine similarity for query-title and query-description matching, keyword overlap, and transparent rule-based intent classification (`informational`, `navigational`, `transactional`, `timely`).
- **Content Quality Evaluation:** Evaluates completeness, Flesch-based readability, keyword relevance (with anti-stuffing checks), usefulness, and repetition/clickbait penalties with human-readable explanations.
- **Transparent Source Credibility Assessment:** Inspects HTTPS usage, domain type, publisher identifiability, author attribution, publication date freshness, and supporting references—explicitly avoiding blind trust in `.gov` or `.edu` domains—while supporting manual reviewer adjustments.
- **Human-Assisted Fact Verification:** Log factual claims, attach supporting evidence and source URLs, and record `Supported`, `Contradicted`, or `Unverified` statuses. Guardrails block marking claims `Supported` or `Contradicted` without adequate evidence and valid source URLs.
- **Configurable Weighted Scoring:** Customize and normalize weights across Relevance (30%), Content Quality (20%), Source Credibility (20%), Factual Evidence (20%), and Intent Alignment (10%). Displays insufficient-evidence warnings when claims are unverified.
- **Automated vs. Human Judgment Separation:** Reviewers can mark results as `Relevant`, `Partially Relevant`, or `Irrelevant`, apply manual score overrides, and add rationale while preserving automated baseline scores.
- **Interactive Streamlit Dashboard & Comparison:** Track total evaluated results, average relevance/quality scores, claim breakdowns, score distributions, and side-by-side Plotly radar/bar comparisons.
- **Local Persistence & Exports:** Save, search, update, and delete evaluation records in local JSON (`data/evaluations.json`), and export CSV summaries, per-result CSV tables, and detailed JSON reports.
- **12 Synthetic Sample Scenarios:** Ready-to-load practice queries across Educational, Technology, Health, Government, and News & Current Events domains using clearly labeled synthetic URLs (`*.invalid` / `example.*`).

---

## Project Architecture

```text
SearchEval/
├── app.py                          # Home Dashboard (metrics, Plotly charts, quick exports)
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Pytest and Ruff configuration
├── README.md                       # Project documentation
├── .env.example                    # Optional local configuration
├── .gitignore
├── .streamlit/
│   └── config.toml                 # Streamlit theme and server config
├── pages/
│   ├── 1_Search_Evaluation.py      # New query & multi-result evaluation + manual overrides
│   ├── 2_Result_Comparison.py      # Radar & side-by-side result comparison
│   ├── 3_Fact_Verification.py      # Evidence-enforced claim verification workflow
│   ├── 4_Evaluation_History.py     # Search, edit, delete, and export saved records
│   └── 5_About.py                  # Methodology, safeguards, and limitations
├── src/
│   ├── evaluator/
│   │   ├── relevance.py            # TF-IDF cosine similarity & rule-based intent alignment
│   │   ├── content_quality.py      # Completeness, readability, usefulness, uniqueness
│   │   ├── credibility.py          # Transparent source signals & manual adjustments
│   │   ├── fact_checker.py         # Human-assisted fact claims & evidence guardrails
│   │   ├── scoring.py              # Normalized weighted scoring & human judgment separation
│   │   └── pipeline.py             # End-to-end session orchestration
│   ├── data/
│   │   ├── storage.py              # Atomic local JSON CRUD & search
│   │   └── sample_data.py          # 12 synthetic scenarios across 5 domains
│   └── utils/
│       ├── validators.py           # Query, URL, date, score validation & duplicate detection
│       ├── exporters.py            # Formula-safe CSV & JSON exporters
│       └── ui.py                   # Shared Streamlit components & styling
├── tests/
│   ├── test_relevance.py
│   ├── test_content_quality.py
│   ├── test_credibility.py
│   ├── test_fact_checker.py
│   ├── test_scoring.py
│   ├── test_storage.py
│   └── test_exporters.py
└── data/
    └── .gitkeep
```

---

## Technology Stack

- **Python 3.11+**
- **Streamlit** (multi-page interactive web interface)
- **Pandas & NumPy** (data wrangling & numerical scoring)
- **Scikit-learn** (`TfidfVectorizer` & `cosine_similarity`)
- **Plotly** (interactive distribution, ranking, and radar charts)
- **Pytest** (unit & integration test suite)
- **Ruff** (linting and code quality)
- **Local JSON & CSV** (storage and exports—no paid APIs or API keys required)

---

## Installation Instructions

1. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional environment configuration:**
   Copy `.env.example` to `.env` if you wish to customize `SEARCHEVAL_DATA_PATH`. No API keys are needed.

---

## How to Run the Application

Start the Streamlit web application locally:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`.

---

## Screenshots

- **Home Dashboard (`app.py`):** KPI summary metrics, score distribution box plots, claim verification bar chart, top-ranked results table, and CSV/JSON archive downloads.
- **New Search Evaluation (`pages/1_Search_Evaluation.py`):** Synthetic sample loader, sidebar weight sliders, multi-result form, automated breakdown cards, and manual reviewer judgment controls.
- **Result Comparison (`pages/2_Result_Comparison.py`):** Multi-dimensional Plotly radar chart and side-by-side score matrix.
- **Fact Verification (`pages/3_Fact_Verification.py`):** Evidence-enforced claim entry form and status summary.

---

## Testing & Code Quality Instructions

Run the complete Pytest suite:
```bash
pytest
```

Run Ruff linting and style checks:
```bash
ruff check .
```

---

## Sample Evaluation Workflow

1. Open **New Search Evaluation** and expand **Load a Synthetic Sample Query**.
2. Choose a scenario (for example, `seasonal influenza prevention guidelines handwashing vaccination`).
3. Adjust scoring weights in the sidebar if desired and click **Run Search Quality Evaluation**.
4. Inspect the automated relevance, content quality, and source credibility breakdowns alongside any insufficient-evidence warnings.
5. Open **Fact Verification** to log or review factual claims with supporting evidence and valid source URLs.
6. Return to apply human reviewer labels (`Relevant`, `Partially Relevant`, `Irrelevant`), optional score overrides, and comments, then click **Apply Judgments & Save Evaluation**.
7. Compare results in **Result Comparison** or export CSV/JSON reports from **Evaluation History**.

---

## Limitations

- Evaluates search snippets and reviewer-supplied metadata rather than crawling external web pages.
- Lexical TF-IDF cosine similarity cannot recognize paraphrased synonyms that share no vocabulary.
- Built-in sample scenarios contain synthetic `.invalid` / `example.*` URLs for training only.

---

## Future Improvements

- Optional local sentence-embedding similarity mode for semantic synonym matching.
- Inter-annotator agreement (Cohen's kappa) comparison across multiple reviewers.
- SQLite backend option for large multi-thousand-record evaluation batches.
