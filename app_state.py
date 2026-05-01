from __future__ import annotations

import json

import streamlit as st

from data_model.schema import ContractModel


def init_state() -> None:
    defaults = {
        "provider": "none",
        "allow_cloud": False,
        "contract_json": None,
        "last_balance": None,
        "artifacts": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_contract(contract: ContractModel) -> None:
    st.session_state["contract_json"] = contract.model_dump(mode="json")


def get_contract() -> ContractModel | None:
    payload = st.session_state.get("contract_json")
    if not payload:
        return None
    if isinstance(payload, str):
        payload = json.loads(payload)
    return ContractModel.model_validate(payload)
