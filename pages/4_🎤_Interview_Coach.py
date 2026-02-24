"""
Page 5 — Interview Coach
Multi-turn behavioral interview session powered by Agent 3.
Reads the FinalReport from st.session_state.
"""

import streamlit as st

from app.config import configure_page, inject_css
from app.panels.interview import render_interview_chat
from app.runner import run_async

configure_page()
inject_css()

st.markdown("# 🎤 Interview Coach")

if "report" not in st.session_state:
    st.warning("No report yet. Go to the **Home** page and run an analysis first.")
    st.stop()

render_interview_chat(st.session_state["report"], run_async)
