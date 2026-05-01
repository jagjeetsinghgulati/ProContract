from __future__ import annotations

import pandas as pd
import streamlit as st

from app_state import get_contract, init_state, set_contract
from auth.session import require_authenticated_user
from pipeline import run_favorability


require_authenticated_user(st)
init_state()

st.title("Party Analysis")
st.caption("Favorability scoring, risk exposure, and contract balance.")

contract = get_contract()
if not contract:
    st.warning("Run Dashboard Phase 1 first to load a contract.")
    st.stop()

if st.button("Run Favorability Analysis"):
    with st.spinner("Scoring favorability and risk..."):
        balance = run_favorability(
            contract,
            provider_name=st.session_state.get("provider", "none"),
            allow_cloud=st.session_state.get("allow_cloud", False),
        )
        st.session_state["last_balance"] = balance
        set_contract(contract)
    st.success("Favorability analysis complete.")

balance = st.session_state.get("last_balance")
if balance:
    c1, c2 = st.columns(2)
    c1.metric("Contract Tilt", balance["tilt_party"])
    c2.metric("Balance Spread", balance["balance_score"])
    st.write("Average favorability by party")
    st.json(balance["averages"])
    st.write("Top imbalanced clause IDs")
    st.write(balance["top_imbalanced_clauses"])

rows = []
for clause in contract.clauses:
    if not clause.favorability:
        continue
    rows.append(
        {
            "heading": clause.heading or clause.clause_id,
            "beneficiary": clause.favorability.beneficiary.value,
            "risk": clause.favorability.risk_level.value,
            "scores": clause.favorability.scores_by_party,
            "reasons": ", ".join(clause.favorability.risk_reasons),
        }
    )

if rows:
    beneficiary_filter = st.multiselect(
        "Beneficiary filter",
        options=sorted({r["beneficiary"] for r in rows}),
        default=sorted({r["beneficiary"] for r in rows}),
    )
    display = [row for row in rows if row["beneficiary"] in beneficiary_filter]
    st.dataframe(pd.DataFrame(display), use_container_width=True)
