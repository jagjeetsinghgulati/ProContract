from __future__ import annotations

import pandas as pd
import streamlit as st

from app_state import get_contract, init_state, set_contract
from auth.session import require_authenticated_user
from data_model.enums import ClauseCategory
from pipeline import run_classification


require_authenticated_user(st)
init_state()

st.title("Clause Browser")
st.caption("Classify clauses and filter by category/criticality/red flags.")

contract = get_contract()
if not contract:
    st.warning("Run Dashboard Phase 1 first to load a contract.")
    st.stop()

if st.button("Run Classification"):
    with st.spinner("Classifying clauses..."):
        contract = run_classification(
            contract,
            provider_name=st.session_state.get("provider", "none"),
            allow_cloud=st.session_state.get("allow_cloud", False),
        )
        set_contract(contract)
    st.success("Classification complete.")

categories = [c.value for c in ClauseCategory]
selected_categories = st.multiselect("Category filter", options=categories, default=categories)
criticality_min, criticality_max = st.slider("Criticality", 1, 5, (1, 5))
red_only = st.checkbox("Show red flags only", value=False)
search_text = st.text_input("Search within clauses")

rows = []
for clause in contract.clauses:
    classification = clause.classification
    if not classification:
        continue
    if classification.primary_category.value not in selected_categories:
        continue
    if not (criticality_min <= classification.criticality.value <= criticality_max):
        continue
    if red_only and not classification.red_flag:
        continue
    if search_text and search_text.lower() not in clause.text.lower():
        continue
    rows.append(
        {
            "clause_id": clause.clause_id,
            "heading": clause.heading,
            "category": classification.primary_category.value,
            "criticality": classification.criticality.value,
            "red_flag": classification.red_flag,
            "confidence": round(classification.confidence, 2),
            "negotiability": classification.negotiability.value,
            "text": clause.text,
            "rationale": classification.rationale,
        }
    )

if not rows:
    st.info("No clauses match current filters.")
else:
    df = pd.DataFrame(rows)
    st.dataframe(
        df[["heading", "category", "criticality", "red_flag", "confidence", "negotiability"]],
        use_container_width=True,
    )
    st.subheader("Clause Details")
    for row in rows:
        with st.expander(f"{row['heading']} | {row['category']}"):
            st.write(row["text"])
            st.caption(f"Rationale: {row['rationale']}")
