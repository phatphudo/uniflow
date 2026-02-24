import json
from retrieval.src.vector_store import add_chunks
from schemas.retrieval import Chunk, record_to_text, category_to_text, extract_degree_abbr

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
    """
    Index one chunk per category per degree for focused, high-quality embeddings.
    Duplicate degree entries in the source JSON are deduplicated by (abbr, category).
    """
    records = json.load(open(json_path))
    chunks = []
    seen_ids: set[str] = set()

    for r in records:
        degree_name = r["degree_name"]
        abbr = extract_degree_abbr(degree_name)
        for cat in r.get("course_requirements", []):
            chunk_id = f"{abbr}::{cat['category']}"
            if chunk_id in seen_ids:
                continue  # skip duplicate degree entries
            seen_ids.add(chunk_id)
            chunks.append(Chunk(
                text=category_to_text(degree_name, abbr, cat),
                source=chunk_id,
                data={
                    "degree_name": degree_name,
                    "degree_abbr": abbr,
                    "category": cat["category"],
                    "credits_required": cat["credits_required"],
                    "courses": cat.get("courses", []),
                    "notes": cat.get("notes", ""),
                },
            ))

    add_chunks(chunks, "requirements")


build_courses_index()
build_requirements_index()
