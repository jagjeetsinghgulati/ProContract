from __future__ import annotations

from pathlib import Path

import streamlit as st

from app_state import get_contract, init_state
from auth.session import require_authenticated_user
from pipeline import run_reporting


require_authenticated_user(st)
init_state()

st.title("Reports")
st.caption("Generate and download clause register, analysis report, change report, and modified contract.")

contract = get_contract()
if not contract:
    st.warning("Run Dashboard Phase 1 first to load a contract.")
    st.stop()

output_dir = st.text_input("Output directory", value="output")
if st.button("Generate Reports"):
    with st.spinner("Creating report artifacts..."):
        artifacts = run_reporting(contract, output_dir=output_dir)
        st.session_state["artifacts"] = artifacts
    st.success("Reports generated.")

artifacts = st.session_state.get("artifacts")
if artifacts:
    st.json(artifacts)
    for label, path in artifacts.items():
        file_path = Path(path)
        if not file_path.exists():
            continue
        with open(file_path, "rb") as handle:
            st.download_button(
                label=f"Download {label}",
                data=handle.read(),
                file_name=file_path.name,
            )
