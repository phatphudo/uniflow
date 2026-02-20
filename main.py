"""
Entry point: `uv run streamlit run main.py`
All logic lives in the app/ package.
"""

import logfire

from app.main import run_app

logfire.configure()
logfire.instrument_pydantic_ai()

run_app()
