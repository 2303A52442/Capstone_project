import re
from typing import Iterable

from app.models.skill import Skill


PROJECT_HEADINGS = re.compile(r"(?:projects?|portfolio)\s*[:\-]?\s*(.*)", re.IGNORECASE)
EDUCATION_HEADINGS = re.compile(r"(?:education|certifications?)\s*[:\-]?\s*(.*)", re.IGNORECASE)


def extract_resume_text(file_bytes: bytes) -> str:
    from io import BytesIO
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if not text:
        raise ValueError("The PDF did not contain extractable text")
    return text


def analyze_text(text: str, skills: Iterable[Skill], source: str, title: str, source_ref: str | None = None) -> dict:
    normalized = text.lower()
    extracted_skills = [
        {"skill_id": skill.id, "name": skill.name, "category": skill.category}
        for skill in skills
        if re.search(r"(?<![a-z0-9])" + re.escape(skill.name.lower()) + r"(?![a-z0-9])", normalized)
    ]
    projects = []
    education = []
    for line in (line.strip() for line in text.splitlines()):
        if not line:
            continue
        project_match = PROJECT_HEADINGS.match(line)
        education_match = EDUCATION_HEADINGS.match(line)
        if project_match and project_match.group(1):
            projects.append({"name": project_match.group(1)[:255], "description": line})
        if education_match and education_match.group(1):
            education.append({"text": education_match.group(1)[:500]})

    return {
        "source": source,
        "source_ref": source_ref,
        "title": title,
        "content": text[:20000],
        "extracted_skills": extracted_skills,
        "extracted_projects": projects,
        "extracted_education": education,
    }
