from __future__ import annotations

import os
import tempfile

import streamlit as st

from app_state import get_contract, init_state, set_contract
from auth.session import require_authenticated_user
from data_model.persistence import save_contract
from pipeline import run_phase1_pipeline


require_authenticated_user(st)
init_state()

st.title("Dashboard")
st.caption("Upload contract, choose provider, and run Phase 1 pipeline.")

provider = st.selectbox("AI Provider", options=["none", "ollama", "lmstudio", "gemini"], index=0)
allow_cloud = st.checkbox("Allow cloud provider (Gemini)", value=False)
st.session_state["provider"] = provider
st.session_state["allow_cloud"] = allow_cloud

uploaded = st.file_uploader("Upload contract", type=["pdf", "docx", "txt"])

if st.button("Run Phase 1", disabled=uploaded is None):
    with st.spinner("Extracting and segmenting contract..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded.name.split('.')[-1]}") as tmp:
            tmp.write(uploaded.getvalue())
            temp_path = tmp.name
        try:
            contract, run = run_phase1_pipeline(
                file_path=temp_path,
                provider_name=provider,
                allow_cloud=allow_cloud and provider == "gemini",
            )
            set_contract(contract)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    st.success("Phase 1 complete.")
    st.json(run.model_dump(mode="json"))

contract = get_contract()
if contract:
    st.subheader("Contract Metadata")
    st.write(f"File: `{contract.file_name}`")
    st.write(f"Clauses extracted: `{len(contract.clauses)}`")
    st.write(f"Detected parties: `{len(contract.parties)}`")

    st.subheader("Party Renaming")
    updated = False
    for idx, party in enumerate(contract.parties):
        new_name = st.text_input(
            f"Party {idx + 1}",
            value=party.display_name,
            key=f"party_name_{party.party_id}",
        )
        if new_name != party.display_name:
            party.display_name = new_name
            updated = True
    if st.button("Save Party Labels") and updated:
        save_contract(contract)
        set_contract(contract)
        st.success("Party names saved.")
