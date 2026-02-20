"""
app/config.py — Page configuration and global CSS injection.
Called once at the very top of main.py before any other st.* calls.
"""

import streamlit as st


def configure_page() -> None:
    """Set Streamlit page config. Must be the first st call in the app."""
    st.set_page_config(
        page_title="UniFlow AI · Career Readiness Engine",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css() -> None:
    """Inject global custom CSS into the running Streamlit page."""
    st.markdown(
        """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Sidebar */
  [data-testid="stSidebar"] {
      background: linear-gradient(160deg, #0f0f1a 0%, #1a1a2e 100%);
      border-right: 1px solid rgba(99,102,241,0.2);
  }

  /* Cards */
  .uniflow-card {
      background: linear-gradient(135deg, #1e1e2e 0%, #16213e 100%);
      border: 1px solid rgba(99,102,241,0.25);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 1rem;
  }
  .uniflow-card:hover {
      border-color: rgba(99,102,241,0.6);
      box-shadow: 0 4px 24px rgba(99,102,241,0.15);
      transition: all 0.25s ease;
  }

  /* Score gauge */
  .score-big {
      font-size: 4.5rem;
      font-weight: 700;
      background: linear-gradient(135deg, #6366f1, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1;
  }

  /* Badge */
  .badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 99px;
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }
  .badge-matched { background: rgba(34,197,94,0.15);  color: #4ade80; border: 1px solid #4ade80; }
  .badge-missing { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid #f87171; }
  .badge-event   { background: rgba(99,102,241,0.15); color: #a78bfa; border: 1px solid #a78bfa; }

  /* Stars row */
  .star-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.5rem; }
  .star-box {
      flex: 1; min-width: 100px;
      background: rgba(99,102,241,0.1);
      border: 1px solid rgba(99,102,241,0.3);
      border-radius: 12px;
      padding: 0.75rem;
      text-align: center;
  }
  .star-label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
  .star-score { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
  .star-max   { font-size: 0.7rem; color: #64748b; }

  /* Section headers */
  h2 { color: #e2e8f0 !important; }
  h3 { color: #c7d2fe !important; }
</style>
""",
        unsafe_allow_html=True,
    )
