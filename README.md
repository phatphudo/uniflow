# UniFlow AI — Career Readiness Engine

A multi-agent AI system that analyzes a student's resume and academic transcript against a target job position, then delivers a complete career readiness report: skill gap analysis, course recommendations, networking events, and behavioral interview coaching.

Built with **PydanticAI**, **ChromaDB**, **Streamlit**, and **Google Gemini**.

---

## Project Structure

```
uniflow-hackathon-2026/
│
├── main.py                     # Streamlit entry point
│
├── ai/                         # All AI/agent logic
│   ├── orchestrator.py         # run_uniflow() — the central pipeline
│   ├── agents/
│   │   ├── deps.py             # OrchestratorDeps — shared dependency injection
│   │   ├── agent1.py           # Position Analyst agent
│   │   ├── agent2.py           # Course & Event Advisor agent (RAG + web search)
│   │   └── agent3.py           # Interview Coach agent (STAR evaluation)
│   └── prompts/
│       ├── agent1_position_analyst.md
│       ├── agent2_advisor.md
│       └── agent3_interview_coach.md
│
├── app/                        # Streamlit UI modules
│   ├── main.py                 # Assembles all panels
│   ├── config.py               # Page config + CSS
│   ├── sidebar.py              # Sidebar inputs → UserInputs dataclass
│   ├── runner.py               # Calls orchestrator, builds deps
│   └── panels/
│       ├── benchmark.py        # Panel 1: Resume Benchmark
│       ├── courses.py          # Panel 2: Course Roadmap
│       ├── events.py           # Panel 3: Events to Attend
│       └── interview.py        # Panel 4: Interview Feedback
│
├── schemas/                    # Pydantic data contracts
│   ├── inputs.py               # StudentInput, TranscriptData
│   ├── agent1.py               # PositionProfile
│   ├── agent2.py               # AdvisorReport, GapReport, CourseRecommendation, EventRecommendation
│   ├── agent3.py               # InterviewResult, StarScores
│   └── report.py               # FinalReport
│
├── docs/
│   └── UniFlow_AI_Blueprint_v3.md
│
├── pyproject.toml
└── uv.lock
```

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Setup

Clone the repo and install all dependencies in one command:

```bash
git clone <repo-url>
cd uniflow-hackathon-2026
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock` and creates an isolated `.venv` automatically — no `pip install` or `python -m venv` needed.

---

## Environment Variables

Copy the example below into a `.env` file at the project root and fill in your keys:

```bash
# .env
GOOGLE_API_KEY=your_google_gemini_api_key
SERPER_API_KEY=your_serper_api_key          # for live event search (Phase 4)
```

> **Phase 1 note:** The app currently runs entirely with mock data — no API keys are required to launch and explore the UI.

---

## Run the App

```bash
uv run streamlit run main.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Development

Run any Python script inside the project environment:

```bash
uv run python <script.py>
```

Add a new dependency:

```bash
uv add <package-name>
```

---

## Architecture Overview

```
Student inputs (resume PDF + transcript PDF + target position)
        ↓
   Orchestrator  (ai/orchestrator.py)
   ┌─────────────────────────────────────┐
   │  Parse → Route → Filter → Assemble  │
   └─────────────────────────────────────┘
        ↓               ↓               ↓
  Agent 1           Agent 2          Agent 3
  Position          Course &         Interview
  Analyst           Event Advisor    Coach
                   (RAG + Search)   (STAR eval)
        ↓               ↓               ↓
        └───────── FinalReport ──────────┘
                        ↓
              Streamlit UI (4 panels)
```

Each agent's system prompt lives in `ai/prompts/*.md` — edit the markdown files to tune agent behavior without touching Python code.
