"""Page 3: Human-Assisted Factual Accuracy Review."""

from __future__ import annotations

import streamlit as st

from src.data.storage import load_evaluations, save_evaluation
from src.evaluator.fact_checker import (
    ClaimStatus,
    summarize_fact_checks,
    validate_and_create_claim,
)
from src.evaluator.pipeline import evaluate_search_session
from src.utils.ui import (
    configure_page,
    ensure_sample_history_seeded,
    render_disclaimer,
    render_sidebar_info,
)

configure_page("Fact Verification", icon="🔍")
render_sidebar_info()

st.title("Human-Assisted Fact Verification")
st.caption(
    "Log factual claims, attach supporting evidence and source URLs, and record human verification "
    "statuses. Claims cannot be marked Supported or Contradicted without adequate evidence."
)
render_disclaimer()

records = ensure_sample_history_seeded()
if not records:
    st.info("No saved evaluations found. Create an evaluation first on **New Search Evaluation**.")
    st.stop()

eval_map = {
    f"{r['query']} ({r.get('category', 'General')} · {r['evaluation_id']})": r
    for r in load_evaluations()
}
selected_key = st.selectbox("Select Evaluation Record to Review Claims", options=list(eval_map.keys()))
selected_eval = eval_map[selected_key]
claims = list(selected_eval.get("claims", []))

summary = summarize_fact_checks(claims)
if summary["insufficient_evidence_warning"]:
    st.warning(summary["insufficient_evidence_warning"])

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Claims", summary["total_claims"])
m2.metric("Supported", summary["supported_count"])
m3.metric("Contradicted", summary["contradicted_count"])
m4.metric("Unverified", summary["unverified_count"])
m5.metric(
    "Evidence Score",
    f"{summary['factual_evidence_score']}/100" if summary["factual_evidence_score"] is not None else "Unverified",
)

st.subheader("Add New Factual Claim")
result_titles = [""] + [r["title"] for r in selected_eval.get("results", [])]

with st.form("add_claim_form", clear_on_submit=True):
    claim_text = st.text_area("Factual Claim to Verify *", height=75, placeholder="Enter a specific factual statement from the search results...")
    linked_title = st.selectbox("Linked Search Result (Optional)", options=result_titles)
    supporting_evidence = st.text_area(
        "Supporting / Refuting Evidence Notes",
        height=85,
        placeholder="Paste concise evidence summary from authoritative reference material (required for Supported/Contradicted).",
    )
    urls_raw = st.text_area(
        "Source URLs (one per line, http:// or https://)",
        height=70,
        placeholder="https://example.org/reference-source",
    )
    status_choice = st.selectbox(
        "Verification Status",
        options=[ClaimStatus.UNVERIFIED.value, ClaimStatus.SUPPORTED.value, ClaimStatus.CONTRADICTED.value],
    )
    reviewer_notes = st.text_input("Reviewer Notes (Optional)")
    submitted = st.form_submit_button("Add Claim to Evaluation", type="primary")

    if submitted:
        url_list = [line.strip() for line in urls_raw.splitlines() if line.strip()]
        new_claim, errors = validate_and_create_claim(
            claim_text=claim_text,
            supporting_evidence=supporting_evidence,
            source_urls=url_list,
            requested_status=status_choice,
            reviewer_notes=reviewer_notes,
            result_title=linked_title,
        )
        if errors:
            for err in errors:
                st.error(err)
        elif new_claim is not None:
            claims.append(new_claim.to_dict())
            updated_eval = evaluate_search_session(
                query=selected_eval["query"],
                results=selected_eval["results"],
                claims=claims,
                weights=selected_eval.get("weights"),
                category=selected_eval.get("category", "General"),
                reviewer_name=selected_eval.get("reviewer_name", "Analyst"),
                session_notes=selected_eval.get("session_notes", ""),
                is_synthetic=selected_eval.get("is_synthetic", False),
                evaluation_id=selected_eval["evaluation_id"],
            )
            save_evaluation(updated_eval)
            st.success("Claim added and evaluation scores updated.")
            st.rerun()

st.subheader("Logged Factual Claims")
if not claims:
    st.info("No factual claims have been added to this evaluation yet.")
else:
    for idx, claim in enumerate(claims):
        status = claim.get("status", ClaimStatus.UNVERIFIED.value)
        badge_cls = (
            "se-badge-human"
            if status == ClaimStatus.SUPPORTED.value
            else ("se-badge-warn" if status == ClaimStatus.CONTRADICTED.value else "se-badge-auto")
        )
        with st.container(border=True):
            st.markdown(
                f'<span class="{badge_cls}">{status.upper()}</span> &nbsp; <strong>{claim.get("claim_text", "")}</strong>',
                unsafe_allow_html=True,
            )
            if claim.get("result_title"):
                st.caption(f"Linked Result: {claim['result_title']}")
            st.write(f"**Evidence:** {claim.get('supporting_evidence') or 'None provided'}")
            urls = claim.get("source_urls") or []
            st.write("**Source URLs:** " + (", ".join(urls) if urls else "None provided"))
            if claim.get("reviewer_notes"):
                st.caption(f"Reviewer Notes: {claim['reviewer_notes']}")

            c1, c2 = st.columns([3, 1])
            with c2:
                if st.button("Delete Claim", key=f"del_claim_{idx}_{claim.get('claim_id', idx)}", use_container_width=True):
                    claims.pop(idx)
                    updated_eval = evaluate_search_session(
                        query=selected_eval["query"],
                        results=selected_eval["results"],
                        claims=claims,
                        weights=selected_eval.get("weights"),
                        category=selected_eval.get("category", "General"),
                        reviewer_name=selected_eval.get("reviewer_name", "Analyst"),
                        session_notes=selected_eval.get("session_notes", ""),
                        is_synthetic=selected_eval.get("is_synthetic", False),
                        evaluation_id=selected_eval["evaluation_id"],
                    )
                    save_evaluation(updated_eval)
                    st.rerun()
