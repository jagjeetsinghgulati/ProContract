from __future__ import annotations

import streamlit as st

from ai_providers.factory import get_factory
from app_state import init_state
from auth.service import login_user, seed_admin_if_missing
from auth.session import create_session, is_authenticated, logout
from config import setup_logging
from data_model.persistence import init_db


setup_logging()
init_db()
seed_admin_if_missing()
init_state()

st.set_page_config(page_title="ProContracts", page_icon="PC", layout="wide")


def render_login() -> None:
    st.title("ProContracts")
    st.caption("Contract Intelligence and Management System")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        user = login_user(username, password)
        if user:
            create_session(st, user.username)
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info("Default seeded admin can be configured in .env (SEED_ADMIN_USERNAME / SEED_ADMIN_PASSWORD).")


def render_home() -> None:
    st.title("ProContracts")
    st.caption("Use the sidebar pages to run the full pipeline.")
    st.write(f"Signed in as: `{st.session_state.get('auth_user', 'unknown')}`")

    if st.button("Logout"):
        logout(st)
        st.rerun()

    st.subheader("Provider Health")
    status = get_factory().check_status()
    st.json(status)

    st.subheader("Workflow")
    st.markdown(
        """
1. Open **Dashboard** and upload contract.
2. Open **Clause Browser** to classify/filter clauses.
3. Open **Party Analysis** for favorability/risk.
4. Open **Modifications** for rewrite proposals.
5. Open **Reports** to export XLSX/DOCX artifacts.
        """
    )


if not is_authenticated(st):
    render_login()
else:
    render_home()
