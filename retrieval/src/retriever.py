from pydantic_ai import Agent
from retrieval.src.vector_store import query as chroma_query
from config import settings
agent =Agent(
    model=settings.ai_model,
    system_prompt="You are a helpful assistant for retrieving relevant information from a vector database based on user queries. You will receive a user query and return the most relevant information from the database.",
)
@agent.tool_plain
def search_documents(query: str) -> list[dict]:
    """
    This function queries the vector database and returns relevant documents based on the user's query.
    """
    return chroma_query(query)