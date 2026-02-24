"""
Page 4 — Events to Attend
Reads the FinalReport from st.session_state and renders the events panel.
"""

import streamlit as st

from app.config import configure_page, inject_css
from app.panels.events import render_events

configure_page()
inject_css()

st.markdown("# 🗓️ Events to Attend")

if "report" not in st.session_state:
    st.warning("No report yet. Go to the **Home** page and run an analysis first.")
    st.stop()

report = st.session_state["report"]
render_events(
    event_recs=report.advisor_report.event_recs,
    calendar_push_ready=report.advisor_report.calendar_push_ready,
)
