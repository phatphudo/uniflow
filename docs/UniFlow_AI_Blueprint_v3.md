# UniFlow AI — Student Lifecycle Engine
**Technical Blueprint · Multi-Agent Architecture · v3.1**
`Track 2: Campus & Career` · `PydanticAI Framework` · `RAG + Web Search` · `3 Agents`

---

## 1. Core Concept & Demo Story

UniFlow AI is a career readiness engine for students. A student provides three things — their **resume**, their **academic transcript**, and a **target position** — and the system returns a complete career readiness report: where they stand, what is missing, which courses to take, which events to attend, and how ready they are to answer interview questions about the role.

> **What makes UniFlow different:**
> Other tools match a resume to a job description. UniFlow goes deeper — it researches the role from first principles, cross-references the student's academic history (transcript) alongside their work history (resume), recommends specific courses from their own college catalog via semantic search, surfaces real-world events to attend for networking and knowledge, and pushes everything to Google Calendar automatically.

### The 90-Second Demo Flow

| Step | Owner | What the User Experiences |
|---|---|---|
| 1 · Input | User → Orchestrator | Student submits resume PDF, transcript PDF, and the position they want |
| 2 · Research | Agent 1 — Position Analyst | System researches the role: required skills, industry scope, common interview topics. Resume and transcript are never seen here. |
| 3 · Filter | Orchestrator | Distils Agent 1's output into a clean skill benchmark, then passes it alongside resume + transcript to Agent 2 |
| 4 · Recommend ✨ | Agent 2 — Course & Event Advisor | Cross-references resume + transcript + benchmark. Runs RAG over college course catalog and live web search for events. Pushes results to Google Calendar. |
| 5 · Coach ✨ | Agent 3 — Interview Coach | Generates a targeted behavioral interview question. Student answers; Coach evaluates using STAR criteria. |
| 6 · Report | Orchestrator → User | Unified output: benchmark score, course & event recommendations with calendar links, STAR interview feedback |

---

## 2. Why PydanticAI

PydanticAI is an agent framework built by the Pydantic team. It handles agent definition, tool registration, structured output validation, and dependency injection natively — all using standard Python type hints. It is the right choice for UniFlow because:

- **Structured outputs by default.** Every agent is declared with a `result_type` — a Pydantic model. The framework forces the LLM to return valid, typed data. No manual JSON parsing, no `try/except` around `json.loads`.
- **Tool registration is clean.** Agent 2's RAG search and web search are registered as `@agent.tool` functions. The LLM decides when to call them; PydanticAI handles the plumbing.
- **Dependency injection.** Shared resources — the ChromaDB client, the Google Calendar service, the parsed resume and transcript — are passed into agents via a typed `RunContext` dependency object. No globals, no hidden state.
- **Model-agnostic.** Swap between `gemini-1.5-pro`, `openai:gpt-4o`, or any supported model in one line.

---

## 3. Data Sources & Knowledge Bases

### 3.1 — Student Inputs (provided at runtime)

| Input | Format | How it is Used |
|---|---|---|
| Resume | PDF | Parsed by Orchestrator via `pdfplumber` → plain text. Passed to Agent 2 as `resume_text`. |
| Academic Transcript | PDF | Parsed by Orchestrator → `TranscriptData` model (completed courses, grades, GPA). Passed to Agent 2. Agent 2 uses this to filter out already-completed courses and check prerequisites. |
| Target Position | String | Typed by the student. Passed exclusively to Agent 1. Agent 1 never sees the resume or transcript. |

### 3.2 — College Course Catalog (RAG via Embeddings)

Ingested once at startup. Queried semantically at runtime by Agent 2's registered tool.

```json
{
  "course_id":    "CS-401",
  "title":        "Machine Learning Fundamentals",
  "department":   "Computer Science",
  "credits":      3,
  "description":  "Covers supervised and unsupervised learning, model evaluation, feature engineering, and neural network basics.",
  "skills_taught":["Python", "scikit-learn", "model evaluation", "feature engineering"],
  "prerequisites":["CS-201", "MATH-301"],
  "schedule":     "MWF 10:00–11:00 AM | Spring semester",
  "open_seats":   12
}
```

**How RAG works:**

1. **Ingestion (once, at startup):** Each course's `title + description + skills_taught` are concatenated, embedded using `sentence-transformers`, and stored in ChromaDB with the full JSON as metadata.
2. **Query (at runtime, inside Agent 2 tool):** The agent constructs a natural-language query from the skill gap and runs a semantic similarity search. Top-k results (k=5) are returned.
3. **Rerank (LLM inside Agent 2):** Filters out courses already in `transcript_data.completed` and those with unmet prerequisites. Final output: 2–3 `CourseRecommendation` objects.

### 3.3 — Live Internet Events (Web Search at Runtime)

Agent 2 uses a registered web search tool (Serper or Tavily) to find professional events — meetups, conferences, workshops, career fairs — relevant to the student's target role and location.

**Search query template:**
```
"{position} networking event OR workshop OR conference {city} {current_month} {year}"
```

For each result, the LLM extracts: title, organiser, date/time, location, registration URL, and a one-sentence relevance reason. Final output: 2–3 `EventRecommendation` objects.

### 3.4 — Google Calendar Integration

After Agent 2 returns recommendations, the Orchestrator pushes approved events to the student's Google Calendar via the Google Calendar API. The student opts in with a single button.

```python
# OAuth2 handled once at startup (credentials.json)
# Scope: https://www.googleapis.com/auth/calendar.events

event_body = {
    "summary":     event.title,
    "location":    event.location,
    "description": f"{event.relevance_reason}\n\nRegister: {event.url}",
    "start":       {"dateTime": event.event_datetime.isoformat(), "timeZone": "America/Chicago"},
    "end":         {"dateTime": event.end_datetime.isoformat(),   "timeZone": "America/Chicago"},
    "reminders":   {"useDefault": False,
                    "overrides":  [{"method": "email",  "minutes": 1440},
                                   {"method": "popup",  "minutes": 60}]}
}
service.events().insert(calendarId="primary", body=event_body).execute()
```

---

## 4. PydanticAI Schemas & Agent Definitions

All inter-agent contracts are Pydantic models. Every PydanticAI agent is declared with a `result_type` that enforces the schema at the framework level.

### 4.1 — Shared Input Models

```python
# schemas/inputs.py
from pydantic import BaseModel, Field

class TranscriptCourse(BaseModel):
    course_id:  str
    title:      str
    grade:      str          # e.g. "A", "B+", "P"
    credits:    float
    semester:   str          # e.g. "Fall 2023"

class TranscriptData(BaseModel):
    student_name: str
    gpa:          float
    completed:    list[TranscriptCourse]
    in_progress:  list[TranscriptCourse] = []

class StudentInput(BaseModel):
    resume_text:     str           = Field(..., description="Raw text parsed from resume PDF")
    transcript_data: TranscriptData
    target_position: str           = Field(..., description="e.g. Product Manager at a tech startup")
```

### 4.2 — Agent 1 Result: PositionProfile

```python
# schemas/agent1.py
from pydantic import BaseModel

class PositionProfile(BaseModel):
    required_skills:      list[str]
    must_have:            list[str]
    nice_to_have:         list[str]
    seniority_indicators: list[str]
    industry_scope:       str        # 2–3 sentence description
    interview_topics:     list[str]
```

### 4.3 — Agent 2 Result: AdvisorReport

```python
# schemas/agent2.py
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class CourseRecommendation(BaseModel):
    course_id:        str
    title:            str
    relevance_reason: str
    skills_covered:   list[str]
    schedule:         str
    open_seats:       int | None = None

class EventRecommendation(BaseModel):
    title:            str
    organiser:        str
    event_datetime:   datetime
    end_datetime:     datetime
    location:         str       # address or "Online"
    url:              HttpUrl
    relevance_reason: str
    event_type:       str       # "networking" | "workshop" | "conference" | "career_fair"

class GapReport(BaseModel):
    benchmark_score:  int       # 0–100
    matched_skills:   list[str]
    missing_skills:   list[str]
    top_gap:          str
    top_gap_evidence: str

class AdvisorReport(BaseModel):
    gap_report:          GapReport
    course_recs:         list[CourseRecommendation]  # 2–3 courses from RAG
    event_recs:          list[EventRecommendation]   # 2–3 events from web search
    calendar_push_ready: bool = True
```

### 4.4 — Agent 3 Result: InterviewResult

```python
# schemas/agent3.py
from pydantic import BaseModel, Field

class StarScores(BaseModel):
    situation: int = Field(..., ge=0, le=25)
    task:      int = Field(..., ge=0, le=25)
    action:    int = Field(..., ge=0, le=25)
    result:    int = Field(..., ge=0, le=25)

    @property
    def total(self) -> int:
        return self.situation + self.task + self.action + self.result

class InterviewResult(BaseModel):
    question:         str
    student_answer:   str
    star_scores:      StarScores
    strengths:        list[str]
    improvements:     list[str]
    stronger_closing: str
```

### 4.5 — Final Report

```python
# schemas/report.py
from pydantic import BaseModel
from .agent1 import PositionProfile
from .agent2 import AdvisorReport
from .agent3 import InterviewResult

class FinalReport(BaseModel):
    student_name:     str
    target_position:  str
    position_profile: PositionProfile
    advisor_report:   AdvisorReport
    interview_result: InterviewResult
    calendar_synced:  bool = False

    @property
    def benchmark_score(self) -> int:
        return self.advisor_report.gap_report.benchmark_score

    @property
    def interview_score(self) -> int:
        return self.interview_result.star_scores.total
```

---

## 5. Multi-Agent Architecture

No agent ever communicates with another directly. Every payload goes through the Orchestrator — this keeps every agent independently testable and integration failures easy to isolate.

```
STUDENT INPUTS
  resume.pdf  +  transcript.pdf  +  target_position
              ↓
    ┌─────────────────────────────┐
    │         ORCHESTRATOR        │
    │  Parse · Route · Filter      │
    └─────────────────────────────┘
         ↓               ↓               ↓
  [position only]  [benchmark +      [top_gap +
                   resume +           interview_topics]
                   transcript]
         ↓               ↓               ↓
   ┌──────────┐   ┌──────────────┐  ┌──────────────┐
   │ Agent 1  │   │   Agent 2    │  │   Agent 3    │
   │ Position │   │ Course &     │  │ Interview    │
   │ Analyst  │   │ Event Advisor│  │ Coach        │
   │          │   │ RAG + Web    │  │ LLM + Whisper│
   └──────────┘   └──────────────┘  └──────────────┘
         ↓               ↓               ↓
  PositionProfile  AdvisorReport   InterviewResult
              ↓
    ┌─────────────────────────────┐
    │  ORCHESTRATOR assembles     │
    │       FinalReport           │
    └─────────────────────────────┘
              ↓
    FINAL REPORT  +  Google Calendar push
```

### Data Flow Table

| # | From | To | Payload |
|---|---|---|---|
| 1 | User | Orchestrator | `StudentInput` (resume_text, transcript_data, target_position) |
| 2 | Orchestrator | Agent 1 | `target_position` only — resume and transcript NOT shared |
| 3 | Agent 1 | Orchestrator | `PositionProfile` |
| 4 | Orchestrator | Agent 2 | FILTERED: `skill_benchmark` + `seniority_level` + `resume_text` + `transcript_data` |
| 5 | Agent 2 | Orchestrator | `AdvisorReport` (GapReport + course_recs + event_recs) |
| 6 | Orchestrator | Agent 3 | `top_gap` + `interview_topics` (from PositionProfile) |
| 7 | Agent 3 | Orchestrator | `InterviewResult` |
| 8 | Orchestrator | Google Calendar | `EventRecommendation` objects → Calendar API push (if opted in) |
| 9 | Orchestrator | User | `FinalReport` |

---

## 6. PydanticAI Agent Definitions

### 6.1 — Dependency Context

PydanticAI passes shared resources into every agent via a typed dependency object. No globals needed.

```python
# agents/deps.py
from dataclasses import dataclass
from chromadb import Collection
from googleapiclient.discovery import Resource
from schemas.inputs import TranscriptData

@dataclass
class OrchestratorDeps:
    resume_text:      str
    transcript_data:  TranscriptData
    course_collection: Collection      # ChromaDB collection
    calendar_service:  Resource        # Google Calendar API client
    search_api_key:    str             # Serper or Tavily key
```

### 6.2 — Agent 1: Position Analyst

```python
# agents/agent1.py
from pydantic_ai import Agent
from schemas.agent1 import PositionProfile

position_analyst = Agent(
    model="gemini-1.5-pro",           # or "openai:gpt-4o"
    result_type=PositionProfile,       # PydanticAI enforces this schema
    system_prompt="""
You are a career research specialist. Given a job title or role description,
produce a structured profile of that position using your training knowledge.
Do NOT reference the student's resume or transcript — your output must be
objective: what the role requires, not what the student has.

Research three areas:
  1. required_skills — classify each as must_have or nice_to_have.
  2. industry_scope — 2-3 sentences on sector, team context, seniority indicators.
  3. interview_topics — behavioural and technical themes common for this role.

Return a valid PositionProfile. No prose outside the schema.
"""
)
```

### 6.3 — Agent 2: Course & Event Advisor

Agent 2 has two registered tools — `search_courses` (RAG) and `search_events` (web). The LLM decides when to call them.

```python
# agents/agent2.py
from pydantic_ai import Agent, RunContext
from agents.deps import OrchestratorDeps
from schemas.agent2 import AdvisorReport
import httpx

advisor = Agent(
    model="gemini-1.5-pro",
    result_type=AdvisorReport,
    deps_type=OrchestratorDeps,
    system_prompt="""
You are a student academic and career advisor.

You receive:
  - skill_benchmark: the must-have skills for the target role
  - seniority_level
  - resume_text: the student's work and project history
  - transcript_data: completed courses, grades, and GPA

STEP 1 — GAP ANALYSIS:
  A skill is 'matched' if it appears in resume_text OR in transcript completed courses.
  benchmark_score = round((matched / total_benchmark_skills) * 100).
  Select top_gap: the single most impactful missing skill.

STEP 2 — COURSE RECOMMENDATIONS:
  Call search_courses(query) with a natural-language query based on missing_skills.
  From results, select 2-3 courses. EXCLUDE courses in transcript completed list.
  EXCLUDE courses whose prerequisites are not in transcript completed list.

STEP 3 — EVENT RECOMMENDATIONS:
  Call search_events(query) to find relevant professional events.
  Select 2-3 highest-relevance events within the next 60 days.

Return a valid AdvisorReport. No prose outside the schema.
"""
)

@advisor.tool
async def search_courses(ctx: RunContext[OrchestratorDeps], query: str) -> list[dict]:
    """Semantic search over the college course catalog in ChromaDB."""
    results = ctx.deps.course_collection.query(
        query_texts=[query],
        n_results=5
    )
    return [
        {**meta, "similarity": dist}
        for meta, dist in zip(
            results["metadatas"][0],
            results["distances"][0]
        )
    ]

@advisor.tool
async def search_events(ctx: RunContext[OrchestratorDeps], query: str) -> list[dict]:
    """Live web search for professional events via Serper API."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": ctx.deps.search_api_key},
            json={"q": query, "num": 10}
        )
    return resp.json().get("organic", [])
```

### 6.4 — Agent 3: Interview Coach

```python
# agents/agent3.py
from pydantic_ai import Agent
from schemas.agent3 import InterviewResult

interview_coach = Agent(
    model="gemini-1.5-pro",
    result_type=InterviewResult,
    system_prompt="""
You are an expert behavioral interview coach. Operate in two phases.

PHASE 1 — QUESTION GENERATION:
  Generate ONE behavioral question targeting the provided top_gap.
  Must: invite a STAR-structured answer, be role-specific, not generic.

  BAD:  "Tell me about a time you managed a project."
  GOOD: "Describe a time you had to align engineering, design, and marketing
         on a launch with competing priorities — how did you keep the team on
         track, and what would you do differently now?"

PHASE 2 — STAR EVALUATION:
  Given the student's answer, evaluate across four dimensions (0-25 each):
    S — Situation: clear context established?
    T — Task: student's specific responsibility explicit?
    A — Action: concrete personal steps described?
    R — Result: measurable or meaningful outcome stated?

  Also provide: strengths[], improvements[], and a stronger_closing example.

Return a valid InterviewResult. No prose outside the schema.
"""
)
```

### 6.5 — Orchestrator

```python
# orchestrator.py
import asyncio
import pdfplumber
from agents.agent1 import position_analyst
from agents.agent2 import advisor
from agents.agent3 import interview_coach
from agents.deps import OrchestratorDeps
from schemas.inputs import StudentInput, TranscriptData
from schemas.report import FinalReport

async def run_uniflow(
    resume_pdf_path:     str,
    transcript_pdf_path: str,
    target_position:     str,
    deps:                OrchestratorDeps,
    student_answer:      str,
) -> FinalReport:

    # ── Step 1: Parse inputs ─────────────────────────────────────────────────
    with pdfplumber.open(resume_pdf_path) as pdf:
        resume_text = "\n".join(p.extract_text() for p in pdf.pages)

    # Transcript parsing — structured into TranscriptData by a parsing utility
    transcript_data = parse_transcript_pdf(transcript_pdf_path)

    # ── Step 2: Agent 1 — Position Analyst ──────────────────────────────────
    agent1_result = await position_analyst.run(target_position)
    position_profile = agent1_result.data   # validated PositionProfile

    # ── Step 3: Orchestrator filters Agent 1 output ──────────────────────────
    skill_benchmark = position_profile.must_have
    seniority_level = position_profile.seniority_indicators[0] if position_profile.seniority_indicators else "mid-level"

    agent2_prompt = f"""
skill_benchmark: {skill_benchmark}
seniority_level: {seniority_level}
resume_text: {resume_text}
transcript_data: {transcript_data.model_dump_json()}
target_position: {target_position}
"""

    # ── Step 4: Agent 2 — Course & Event Advisor ────────────────────────────
    agent2_result = await advisor.run(agent2_prompt, deps=deps)
    advisor_report = agent2_result.data     # validated AdvisorReport

    # ── Step 5: Agent 3 — Interview Coach ───────────────────────────────────
    top_gap = advisor_report.gap_report.top_gap
    agent3_prompt = f"""
top_gap: {top_gap}
interview_topics: {position_profile.interview_topics}
position_context: {target_position}
student_answer: {student_answer}
"""
    agent3_result = await interview_coach.run(agent3_prompt)
    interview_result = agent3_result.data   # validated InterviewResult

    # ── Step 6: Google Calendar push (if opted in) ───────────────────────────
    if advisor_report.calendar_push_ready:
        for event in advisor_report.event_recs:
            push_to_calendar(deps.calendar_service, event)

    # ── Step 7: Assemble FinalReport ─────────────────────────────────────────
    return FinalReport(
        student_name=transcript_data.student_name,
        target_position=target_position,
        position_profile=position_profile,
        advisor_report=advisor_report,
        interview_result=interview_result,
        calendar_synced=advisor_report.calendar_push_ready,
    )
```

---

## 7. Final Report — What the Student Sees

| Panel | Source | Content |
|---|---|---|
| **Resume Benchmark** | `AdvisorReport.gap_report` | Score 0–100 as a visual gauge. Matched vs. missing skills side by side. |
| **Course Roadmap** | `AdvisorReport.course_recs` | 2–3 course cards: name, schedule, open seats, why it closes the gap. "Add to Calendar" per course start date. |
| **Events to Attend** | `AdvisorReport.event_recs` | 2–3 event cards: title, date, location, event_type badge. "Add All to Calendar" triggers Google Calendar API push. |
| **Interview Feedback** | `InterviewResult` | Question asked, student's answer, STAR scorecard with per-dimension scores, strengths, improvements, stronger_closing example. |

---

## 8. Seven-Day Build Timeline

> **Skeleton-first rule:** By end of Day 1, every PydanticAI agent must exist and return a hardcoded valid result object. The FinalReport must render in the UI with fake data. This is the contract — nothing ships on Day 7 that isn't wired to this contract by Day 1.

| Day | Focus | Build | Done When |
|---|---|---|---|
| **Day 1** | Skeleton | All schemas defined · All PydanticAI agents declared with `result_type` · Agents return hardcoded valid objects · FinalReport renders in Streamlit | Full demo flow works with mocked data |
| **Day 2** | Agent 1 | Real `position_analyst` prompt tuned · Test with 5 role titles · `PositionProfile` validates correctly · Orchestrator filter logic written | Real position profiles for any job title |
| **Day 3** | RAG Setup | ChromaDB ingestion script for course JSON · `sentence-transformers` embeddings · `search_courses` tool returns top-5 results · Transcript parsing (pdfplumber) | Semantic query returns relevant courses; completed courses filtered |
| **Day 4** | Agent 2 | Full `advisor` prompt · Gap analysis logic · `search_events` tool (Serper/Tavily) · `AdvisorReport` validates end-to-end | Real resume + transcript → real course + event recs |
| **Day 5** | Agent 3 + Calendar | `interview_coach` prompt · STAR evaluation · Whisper audio path (optional) · Google Calendar OAuth + push · UI calendar button | Interview feedback works; events push to calendar |
| **Day 6** | Integration | Full Orchestrator `run_uniflow` wired · PydanticAI validation on all agents · Retry on malformed output · Edge cases tested · UI polish | No crashes on any demo path; all 4 panels render |
| **Day 7** | Demo Prep | Rehearse 90-sec pitch · Pre-load sample resume + transcript + position · Screenshots as backup · Designate operator vs. presenter | Team demos confidently without notes |

---

## 9. Team Role Assignments

| Role | Primary Skills | Owns |
|---|---|---|
| **Orchestrator Lead** | Python, PydanticAI, LLM APIs | `run_uniflow` flow · `OrchestratorDeps` · filtering logic · Google Calendar push · `FinalReport` assembly. Most critical role. |
| **Agent 1 + RAG** | Python, embeddings, ChromaDB | `position_analyst` prompt · ChromaDB ingestion script · `search_courses` tool · transcript parsing · course filtering logic |
| **Agent 2 + Frontend** | Python, Streamlit, web search | `advisor` prompt · `search_events` tool (Serper/Tavily) · `AdvisorReport` assembly · all 4 UI panels · benchmark gauge · calendar button |
| **Agent 3 *** | Python, audio, prompting | `interview_coach` prompt · STAR evaluation · Whisper transcription · audio input. Can be handled by Orchestrator Lead for a 3-person team. |

---

> **Define the schemas on Day 1. Everything else is plumbing.**
> The `result_type` on each PydanticAI agent is the contract between every teammate — lock it early and build against it in parallel.
