from __future__ import annotations

import streamlit as st

from app_state import get_contract, init_state, set_contract
from auth.session import require_authenticated_user
from data_model.enums import FavorabilityTarget, ModificationMode
from data_model.persistence import save_contract
from pipeline import run_modification


require_authenticated_user(st)
init_state()

st.title("Modification Workshop")
st.caption("Generate clause rewrites and manage accept/reject decisions.")

contract = get_contract()
if not contract:
    st.warning("Run Dashboard Phase 1 first to load a contract.")
    st.stop()

mode = st.selectbox("Mode", options=[m.value for m in ModificationMode], index=0)
target = st.selectbox("Target Party", options=[t.value for t in FavorabilityTarget], index=0)

if st.button("Generate Modifications"):
    with st.spinner("Generating modifications..."):
        contract = run_modification(
            contract=contract,
            mode=ModificationMode(mode),
            target_party=FavorabilityTarget(target),
            provider_name=st.session_state.get("provider", "none"),
            allow_cloud=st.session_state.get("allow_cloud", False),
        )
        set_contract(contract)
    st.success("Modifications generated.")

for clause in contract.clauses:
    if not clause.modifications:
        continue
    latest = clause.modifications[-1]
    with st.expander(clause.heading or clause.clause_id):
        left, right = st.columns(2)
        with left:
            st.caption("Original")
            st.write(clause.text)
        with right:
            st.caption("Proposed")
            st.write(latest.proposed_text)
            decision = st.selectbox(
                "Decision",
                options=["Pending", "Accepted", "Rejected"],
                index=["Pending", "Accepted", "Rejected"].index(latest.accept_status),
                key=f"decision_{latest.proposal_id}",
            )
            latest.accept_status = decision
            st.caption(latest.change_summary)

if st.button("Save Decisions"):
    save_contract(contract)
    set_contract(contract)
    st.success("Modification decisions saved.")
