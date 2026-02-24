from pydantic import BaseModel



class Chunk(BaseModel):
    text: str
    source: str
    data: dict

def record_to_text(r: dict) -> str:
    skills = ", ".join(r.get("skills_taught", []))
    prereqs = ", ".join(r.get("prerequisites", [])) or "None"
    return (
        f"Course: {r['title']} ({r['course_id']}) | "
        f"Department: {r['department']} | "
        f"Credits: {r['credits']} | "
        f"Description: {r['description']} | "
        f"Skills: {skills} | "
        f"Prerequisites: {prereqs}"
    )

def requirement_to_text(r: dict) -> str:
    parts = [f"Degree: {r['degree_name']} | Total credits: {r['credits_to_graduate']}"]
    for cat in r.get("course_requirements", []):
        course_titles = ", ".join(
            f"{c['code']} {c['title']}" for c in cat.get("courses", [])
        )
        parts.append(
            f"Category: {cat['category']} ({cat['credits_required']} credits) | "
            f"Courses: {course_titles or 'See elective notes'}"
        )
    return " || ".join(parts)


