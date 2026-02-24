from pydantic_ai import Agent
from retrieval.src.vector_store import query as chroma_query
from ai.prompts import load_prompt
from config import settings

_SYSTEM_PROMPT = load_prompt("retrierver_prompt")

_agent = None


def agent():
    """Return the retrieval agent, creating it on first call."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=settings.ai_model,
            system_prompt=_SYSTEM_PROMPT,
        )

        @_agent.tool_plain
        def search_documents(query: str) -> list[dict]:
            """Search the courses catalog for courses matching the query."""
            return chroma_query(query, "courses")

        @_agent.tool_plain
        def search_requirements(query: str) -> list[dict]:
            """Search degree requirements for programs matching the query."""
            return chroma_query(query, "requirements")

    return _agent
