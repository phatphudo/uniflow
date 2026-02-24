# UniFlow Current Code Context

This document summarizes the **current repository state** (as of this snapshot) so you can quickly understand how the app works end-to-end.

## 1. What This App Does

UniFlow is a Streamlit app that produces a career-readiness report from:
- target position
- resume PDF
- transcript PDF
- interview answer

Output is a `FinalReport` with:
- role profile (Agent 1)
- skill-gap + courses + events (Agent 2)
- STAR interview feedback (Agent 3)

## 2. High-Level Runtime Flow

1. `main.py`
- Configures Logfire instrumentation.
- Calls `app.main.run_app()`.

2. `app/main.py`
- Sets Streamlit page config and CSS.
- Reads sidebar user inputs.
- Calls `run_analysis(inputs)`.
- Renders 4 panels from returned `FinalReport`.

3. `app/runner.py`
- Builds stub dependencies (`build_stub_deps()`).
- Calls `asyncio.run(run_uniflow(..., use_mocks=True))`.

4. `ai/orchestrator.py::run_uniflow(...)`
- Parses inputs (stub parser in mock mode).
- Runs Agent 1 block.
- Runs Agent 2 block.
- Runs Agent 3 block.
- Optionally pushes events to calendar (stub).
- Assembles and returns `FinalReport`.

Important: current UI path uses `use_mocks=True`, so production agent calls are bypassed in normal app run.

## 3. Folder Responsibilities

### `app/` (UI layer)
- `app/main.py`: orchestrates UI composition.
- `app/sidebar.py`: user input collection (role, files, text answer).
- `app/runner.py`: bridge from UI to orchestrator.
- `app/config.py`: page setup + global CSS.
- `app/panels/*.py`: report rendering panels.

### `ai/` (logic + agents)
- `ai/orchestrator.py`: end-to-end pipeline coordination.
- `ai/agents/agent1.py`: Position Analyst agent + mock output.
- `ai/agents/agent2.py`: Advisor agent + tools + mock output.
- `ai/agents/agent3.py`: Interview Coach agent + audio record/transcribe helpers + mock output.
- `ai/agents/deps.py`: runtime dependency container (`OrchestratorDeps`).
- `ai/prompts/*.md`: system prompts loaded by agents.

### `schemas/` (data contracts)
Pydantic models shared across UI, orchestrator, and agents.
- `schemas/inputs.py`
- `schemas/agent1.py`
- `schemas/agent2.py`
- `schemas/agent3.py`
- `schemas/report.py`

### root config/deps
- `config.py`: settings loaded from `.env`.
- `pyproject.toml`: package metadata + dependencies.
- `requirements.txt`: pip-style dependency list.
- `.env.example`: environment variable template.

## 4. Agent-by-Agent Behavior

## Agent 1 (`ai/agents/agent1.py`)
Purpose:
- Build a `PositionProfile` from target role description.

Key function:
- `get_position_analyst()` lazily creates singleton `Agent(model=settings.ai_model, output_type=PositionProfile, system_prompt=...)`.

Current app behavior:
- In mock mode, orchestrator uses `MOCK_POSITION_PROFILE`.

## Agent 2 (`ai/agents/agent2.py`)
Purpose:
- Build `AdvisorReport` containing gap report, course recs, event recs.

Key function:
- `get_advisor()` lazily creates singleton `Agent(..., output_type=AdvisorReport, deps_type=OrchestratorDeps)`.

Registered tools:
- `search_courses(...)`: queries `ctx.deps.course_collection` (Chroma-style API).
- `search_events(...)`: Serper HTTP API via `ctx.deps.search_api_key`.

Current app behavior:
- In mock mode, orchestrator uses `MOCK_ADVISOR_REPORT`.

## Agent 3 (`ai/agents/agent3.py`)
Purpose:
- Produce `InterviewResult` STAR feedback.

Key function:
- `get_interview_coach()` lazily creates singleton `Agent(model=settings.ai_model, output_type=InterviewResult, system_prompt=...)`.

Audio helper functions (currently local utility functions):
- `record_student_answer(...)`: records microphone audio and writes WAV.
- `transcribe_student_answer(...)`: transcribes audio with OpenAI STT model.

Current app behavior:
- In mock mode, orchestrator uses `MOCK_INTERVIEW_RESULT`.
- Audio helpers are not integrated into Streamlit flow yet.

## 5. Data Models (Current Contracts)

### Input-side
- `TranscriptCourse`, `TranscriptData`, `StudentInput` in `schemas/inputs.py`.

### Agent 1 output
- `PositionProfile` in `schemas/agent1.py`.

### Agent 2 output
- `GapReport`, `CourseRecommendation`, `EventRecommendation`, `AdvisorReport` in `schemas/agent2.py`.

### Agent 3 output
- `StarScores` with strict `0..25` bounds on each STAR dimension.
- `InterviewResult` with `question`, `student_answer`, `strengths`, `improvements`, etc.
- `Agent3Input` currently exists but is not wired into orchestrator/UI.

### Final aggregate
- `FinalReport` in `schemas/report.py`.
- Computed properties:
  - `benchmark_score`
  - `interview_score` (= STAR total)

## 6. Prompts

- `ai/prompts/agent1_position_analyst.md`
- `ai/prompts/agent2_advisor.md`
- `ai/prompts/agent3_interview_coach.md`

`ai/prompts/__init__.py::load_prompt(name)` loads prompt text by filename and fails fast if missing.

## 7. Configuration + Environment

`config.py` uses `pydantic-settings` with `.env` loading.

Current settings fields:
- `ai_model` (default `openai:gpt-4o`)
- `agent3_model` (default `openai:gpt-4o-tts`)
- `stt_model` (default `gpt-4o-mini-transcribe`)
- `openai_api_key`
- `serper_api_key`

`.env.example` also includes:
- `AI_MODEL`
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `LOGFIRE_TOKEN`

## 8. What Is Mock vs Real Right Now

Current default run path (`uv run streamlit run main.py`):
- Uses mock outputs from all three agents through `use_mocks=True` in `app/runner.py`.
- Uses stub transcript parser.
- Uses stub calendar push.

Real path exists in orchestrator but depends on:
- parsed resume text from actual PDF
- real transcript parsing (currently still stubbed)
- real deps for `course_collection`, `calendar_service`, `search_api_key`
- API keys + model/provider config

## 9. Known Gaps / Risks in Current Snapshot

1. `app/runner.py` passes uploaded file names, not persisted file paths.
- If `use_mocks=False`, PDF parsing likely fails unless files are saved first.

2. `OrchestratorDeps` in UI runner are placeholder values.
- `course_collection=None` and empty search key block Agent 2 tools in real mode.

3. `agent3_model` setting is defined but `agent3.py` currently uses `settings.ai_model` in `get_interview_coach()`.
- If separate model selection is intended for Agent 3, this is not yet wired.

4. `record_student_answer` is declared `async` but internally uses blocking audio calls.
- Works functionally, but it is not truly non-blocking.

5. `schemas/agent3.py::InterviewResult.result` returns a dict with string key `"star_scores.total"`.
- Works, but key naming may be awkward for downstream consumers.

6. `requirements.txt` may drift from `pyproject.toml` if maintained manually.
- `pyproject.toml` remains source of truth for `uv` workflows.

## 10. How to Read the Code Quickly (Suggested Order)

1. `app/main.py`
2. `app/sidebar.py`
3. `app/runner.py`
4. `ai/orchestrator.py`
5. `schemas/report.py` then `schemas/agent1.py`, `schemas/agent2.py`, `schemas/agent3.py`
6. `ai/agents/agent1.py`, `agent2.py`, `agent3.py`
7. `ai/prompts/*.md`
8. `config.py`

## 11. Current Dependency Surface (from `pyproject.toml`)

Core packages:
- `streamlit`
- `pydantic-ai`
- `openai`
- `sounddevice`
- `httpx`
- `pdfplumber`
- `chromadb`
- `google-api-python-client`
- `google-auth-oauthlib`
- `sentence-transformers`
- `python-dotenv`
- `logfire`

## 12. Practical Summary

The architecture is cleanly separated:
- UI (`app/`)
- orchestration/agent logic (`ai/`)
- strict typed contracts (`schemas/`)

The app is currently in a hybrid state:
- production structure exists,
- default execution is still mock-driven,
- several integration points (file persistence, real deps, calendar wiring, full Agent 3 runtime flow) still need completion before full production deployment.
