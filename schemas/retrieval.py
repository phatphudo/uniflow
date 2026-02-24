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

def extract_degree_abbr(degree_name: str) -> str:
    """Extract abbreviation from degree name, e.g. 'Bachelor of Science in CS (BSCS)' → 'BSCS'."""
    import re
    m = re.search(r'\(([A-Z]+)\)', degree_name)
    return m.group(1) if m else degree_name.split()[-1]


def category_to_text(degree_name: str, abbr: str, category: dict) -> str:
    """
    Produce focused, embeddable text for one degree category.
    One chunk per category gives better semantic retrieval than one blob per degree.
    """
    courses = " | ".join(
        f"{c['code']}: {c['title']} ({c.get('credits', 3)} cr)"
        for c in category.get("courses", [])
    )
    notes = category.get("notes", "")
    text = (
        f"{abbr} {degree_name} — {category['category']} "
        f"({category['credits_required']} credits required)"
    )
    if courses:
        text += f" | Courses: {courses}"
    if notes:
        text += f" | Notes: {notes}"
    return text


