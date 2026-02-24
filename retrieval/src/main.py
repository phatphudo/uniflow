import json
from retrieval.src.vector_store import add_chunks
from schemas.retrieval import Chunk, record_to_text, requirement_to_text

COURSES_PATH = "/Users/Local Documents/uniflow/retrieval/data/processed/courses.json"
REQUIREMENTS_PATH = "/Users/Local Documents/uniflow/retrieval/data/processed/requirements.json"


def build_courses_index(json_path=COURSES_PATH):
    records = json.load(open(json_path))
    chunks = [
        Chunk(
            text=record_to_text(r),
            source=r["course_id"],
            data=r
        )
        for r in records
    ]
    add_chunks(chunks, "courses")


def build_requirements_index(json_path=REQUIREMENTS_PATH):
    records = json.load(open(json_path))
    chunks = [
        Chunk(
            text=requirement_to_text(r),
            source=f"{r['degree_name']}_{i}",
            data=r
        )
        for i, r in enumerate(records)
    ]
    add_chunks(chunks, "requirements")


build_courses_index()
build_requirements_index()
