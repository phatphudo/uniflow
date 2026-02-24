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

All settings are managed via [`config.py`](config.py) using **pydantic-settings**.

Create your local `.env` from the provided example:

```bash
cp .env.example .env
```

Then open `.env` and fill in the values you need:

| Variable | Required for | Where to get it |
|---|---|---|
| `AI_MODEL` | All phases | Set to `google-gla:gemini-1.5-pro` (default) or `openai:gpt-4o` |
| `GOOGLE_API_KEY` | AI_MODEL = `google-gla:*` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | AI_MODEL = `openai:*` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `SERPER_API_KEY` | Phase 4+ (live events) | [Serper](https://serper.dev) |

> **Phase 1 note:** The app runs entirely with mock data out of the box — no API keys are required to launch and explore the UI.

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
Student inputs (target role + resume PDF + transcript PDF
              + program enrolled + credits remaining + interview answer)
        ↓
Streamlit UI (app/sidebar.py, app/runner.py)
        ↓
Orchestrator (ai/orchestrator.py)
┌────────────────────────────────────────────────────────────────────┐
│ Parse inputs → Agent routing → Result merge → FinalReport build   │
└────────────────────────────────────────────────────────────────────┘
        ↓                     ↓                          ↓
   Agent 1                Agent 2                    Agent 3
Position Analyst      Advisor (Gap +             Interview Coach
 PositionProfile     Study Plan + Events)     (Question/TTS/STT + STAR eval)
        │                    │                          │
        │          ┌─────────┴──────────┐               │
        │          │   search_courses   │               │
        │          │        ↓           │               │
        │          │   Retriever Agent  │               │
        │          │  (retriever.py)    │               │
        │          │   ┌────────────┐   │               │
        │          │   │ get_degree │   │               │
        │          │   │ _require-  │   │               │
        │          │   │ ments      │   │               │
        │          │   │ (JSON)     │   │               │
        │          │   ├────────────┤   │               │
        │          │   │ search_    │   │               │
        │          │   │ documents  │   │               │
        │          │   │ (ChromaDB) │   │               │
        │          │   └────────────┘   │               │
        │          │        ↓           │               │
        │          │  Flat course list  │               │
        │          │        ↓           │               │
        │          │  Semester packing  │               │
        │          │  (Python logic)    │               │
        │          └────────────────────┘               │
        │                    │                          │
        │              study_plan +                     │
        │            gap_report + events                │
        │                    │                          │
        └────────────────────┴────────── FinalReport ───┘
                                     ↓
                           Streamlit panels (4)
```

Each agent's system prompt lives in `ai/prompts/*.md` — edit the markdown files to tune agent behavior without touching Python code.

Run Flow:
Orchestrator.run_uniflow()
  │
  ├─ Agent1.run()          ← LLM + no tools that call agents
  │
  ├─ Agent2.run()          ← LLM
  │     │
  │     ├─ search_courses()   ← Python async tool
  │     │     │
  │     │     └─ retriever_agent().run()   ← LLM (sub-agent, called ONCE)
  │     │           │
  │     │           ├─ get_degree_requirements()  ← Pure Python (JSON file)
  │     │           └─ search_documents()         ← Pure Python (ChromaDB)
  │     │
  │     └─ search_events()    ← Python async tool (HTTP call only)
  │
  └─ Agent3.generate_question()  ← LLM + no tools that call agents
