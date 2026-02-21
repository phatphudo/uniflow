import chromadb, os
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import json
from src.utils import Chunk
def get_collection():
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    client = chromadb.PersistentClient(path="vector_db", embedding_function=embedding_fn)
    return client.get_or_create_collection(
        name="documents",
        embedding_function=embedding_fn)



def add_chunks(chunks: list[Chunk]):
    collection = get_collection()
    collection.add(
        ids=[c.source for c in chunks],
        documents=[c.text for c in chunks],         # used for embedding & search
        metadatas=[{"data": json.dumps(c.data)} for c in chunks]  # full JSON preserved here
    )

def query(text: str, k=5) -> list[dict]:
    collection = get_collection()
    results = collection.query(query_texts=[text], n_results=k)
    return [
        json.loads(meta["data"])                    # returns your original JSON format
        for meta in results["metadatas"][0]
    ]