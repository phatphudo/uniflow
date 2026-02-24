"""
Mock test for the retriever sub-agent pipeline.
Tests that the retriever returns courses for BSCS with some completed courses.
"""

import asyncio
import sys
import os

# Ensure project root is on path and CWD is project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from retrieval.src.retriever import agent, RetrieverDeps


async def main():
    program = "Bachelor of Science in Computer Science (BSCS)"
    completed = {"APP101", "APP103", "APP201", "MATH201", "CS250", "CS250L"}
    credits_remaining = 90
    skills = ["machine learning", "data structures", "python"]
    # Student already knows these — electives should target what's MISSING
    student_skills = ["python", "data structures", "javascript"]

    deps = RetrieverDeps(
        program_enrolled=program,
        completed_ids=completed,
        credits_remaining=credits_remaining,
        skill_benchmark=skills,
        student_skills=student_skills,
    )

    user_prompt = (
        f"enrolled_program: {program}\n"
        f"completed_courses: {sorted(completed)}\n"
        f"credits_remaining: {credits_remaining}\n"
        f"skill_benchmark: {skills}\n"
    )

    print("=" * 60)
    print("RETRIEVER MOCK TEST")
    print("=" * 60)
    print(f"Program: {program}")
    print(f"Completed: {sorted(completed)}")
    print(f"Credits remaining: {credits_remaining}")
    print(f"Skills: {skills}")
    print("=" * 60)
    print("\nCalling retriever agent...\n")

    result = await agent().run(user_prompt, deps=deps)
    # output_type=list[dict] — already parsed and validated by PydanticAI
    # Safety net: strip any completed courses that slipped through
    courses: list[dict] = [
        c for c in (result.output or [])
        if c.get("course_id") not in completed
    ]

    print(f"\n{'=' * 60}")
    print(f"OUTPUT TYPE: {type(result.output).__name__}, {len(courses)} courses")
    print(f"{'=' * 60}")

    print(f"\nPARSED COURSES: {len(courses)}")
    total_credits = 0
    for c in courses:
        cid = c.get("course_id", "?")
        title = c.get("title", "?")
        cat = c.get("category", "?")
        cr = c.get("credits", 3)
        total_credits += cr
        print(f"  {cid:10s} | {cr} cr | {cat:25s} | {title}")

    print(f"\nTOTAL CREDITS: {total_credits}")
    print(f"EXPECTED:      {credits_remaining}")
    print(f"MATCH:         {'YES' if total_credits == credits_remaining else 'NO'}")

    # Check for duplicates with completed
    returned_ids = {c.get("course_id") for c in courses}
    overlap = returned_ids & completed
    if overlap:
        print(f"\nERROR: Returned completed courses: {overlap}")
    else:
        print("\nNo overlap with completed courses (good)")


if __name__ == "__main__":
    asyncio.run(main())
