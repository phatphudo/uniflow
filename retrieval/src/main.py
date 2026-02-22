import argparse
from pathlib import Path
from retriever import agent
from src.vector_store import add_chunks
import json
from schemas.retrieval import Chunk, record_to_text
def build_index(json_path="data/raw/courses.json"):
    records = json.load(open(json_path))
    chunks = [
        Chunk(
            text=record_to_text(r),   # only used for semantic search
            source=r["course_id"],
            data=r                    # full original record stored here
        )
        for i, r in enumerate(records)
    ]
    add_chunks(chunks)


build_index()