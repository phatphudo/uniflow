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

