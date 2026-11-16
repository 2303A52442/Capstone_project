from app.models.skill import Skill
from app.services.evidence_analysis import analyze_text


def test_external_evidence_extracts_known_skills_and_sections_without_inventing_data():
    skills = [
        Skill(id=1, name="Python", category="Programming"),
        Skill(id=2, name="PostgreSQL", category="Data"),
    ]

    result = analyze_text(
        "Projects: Career Twin API\nBuilt services with Python and PostgreSQL.\nEducation: BSc Computer Science",
        skills,
        "Resume",
        "resume.pdf",
    )

    assert [item["name"] for item in result["extracted_skills"]] == ["Python", "PostgreSQL"]
    assert result["extracted_projects"] == [{"name": "Career Twin API", "description": "Projects: Career Twin API"}]
    assert result["extracted_education"] == [{"text": "BSc Computer Science"}]
