import json
import unittest
from unittest.mock import patch

from schemas.retrieval import Chunk
from retrieval.src import vector_store


class _FakeCollection:
    def __init__(self, query_payload=None):
        self.add_kwargs = None
        self.query_kwargs = None
        self._query_payload = query_payload or {"metadatas": [[]]}

    def add(self, **kwargs):
        self.add_kwargs = kwargs

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return self._query_payload


class TestVectorStore(unittest.TestCase):
    def test_add_chunks_serializes_chunk_data(self):
        fake = _FakeCollection()
        chunks = [
            Chunk(
                text="Course: Product Strategy",
                source="BUS-412",
                data={"course_id": "BUS-412", "title": "Product Strategy"},
            ),
            Chunk(
                text="Course: Data Analysis",
                source="CS-305",
                data={"course_id": "CS-305", "title": "Applied Data Analysis"},
            ),
        ]

        with patch.object(vector_store, "get_collection", return_value=fake):
            vector_store.add_chunks(chunks)

        print("add_chunks payload:", fake.add_kwargs)
        self.assertIsNotNone(fake.add_kwargs)
        self.assertEqual(fake.add_kwargs["ids"], ["BUS-412", "CS-305"])
        self.assertEqual(
            fake.add_kwargs["documents"],
            ["Course: Product Strategy", "Course: Data Analysis"],
        )
        self.assertEqual(
            fake.add_kwargs["metadatas"],
            [
                {"data": json.dumps(chunks[0].data)},
                {"data": json.dumps(chunks[1].data)},
            ],
        )

    def test_query_deserializes_metadata_json(self):
        full_course_1 = {
            "course_id": "BUS-412",
            "title": "Product Strategy & Roadmapping",
            "department": "Business",
            "credits": 3,
            "skills_taught": ["Roadmapping", "Stakeholder Management"],
            "prerequisites": ["BUS-201"],
        }
        full_course_2 = {
            "course_id": "CS-305",
            "title": "Applied Data Analysis",
            "department": "Computer Science",
            "credits": 3,
            "skills_taught": ["SQL", "A/B Testing"],
            "prerequisites": ["CS-101", "MATH-101"],
        }

        fake = _FakeCollection(
            query_payload={
                "metadatas": [
                    [
                        {"data": json.dumps(full_course_1)},
                        {"data": json.dumps(full_course_2)},
                    ]
                ]
            }
        )

        with patch.object(vector_store, "get_collection", return_value=fake):
            results = vector_store.query("roadmap course", k=2)

        print("query results:", results)
        print("query kwargs:", fake.query_kwargs)
        self.assertEqual(
            results,
            [full_course_1, full_course_2],
        )
        self.assertEqual(
            fake.query_kwargs,
            {"query_texts": ["roadmap course"], "n_results": 2},
        )


if __name__ == "__main__":
    unittest.main()
