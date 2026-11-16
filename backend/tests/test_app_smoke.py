from app.main import app
from app.services.recommendation_engine import generate_recommendation


def test_app_starts():
    assert app is not None
    assert app.title == "AI Career Twin API"


def test_recommendation_prioritizes_role_importance_and_evidence():
    recommendation = generate_recommendation(
        candidate_skill_metrics=[
            {
                "skill_name": "Skill A",
                "current_level": 1.0,
                "confidence": 0.5,
                "recency": 0.1,
            },
            {
                "skill_name": "Skill B",
                "current_level": 3.0,
                "confidence": 0.9,
                "recency": 1.0,
            },
        ],
        target_role_skills=[
            {"skill_name": "Skill A", "required_level": 3.0, "importance": 1.0},
            {"skill_name": "Skill B", "required_level": 4.0, "importance": 5.0},
        ],
    )

    assert recommendation is not None
    assert recommendation["target_skill"] == "Skill B"
    assert recommendation["priority_score"] > 0
