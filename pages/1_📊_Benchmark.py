"""
Page 2 — Resume Benchmark
Reads the FinalReport from st.session_state and renders the benchmark panel.
"""

import streamlit as st

from app.config import configure_page, inject_css
from app.panels.benchmark import render_benchmark

configure_page()
inject_css()

st.markdown("# 📊 Resume Benchmark")

if "report" not in st.session_state:
    st.warning("No report yet. Go to the **Home** page and run an analysis first.")
    st.stop()

render_benchmark(st.session_state["report"].advisor_report.gap_report)
