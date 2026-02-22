"""
Entry point: `uv run streamlit run main.py`
All logic lives in the app/ package.
"""

import logfire

from app.main import run_app
from config import settings

logfire.configure(token=settings.logfire_token, environment=settings.env)
logfire.instrument_pydantic_ai()

run_app()
