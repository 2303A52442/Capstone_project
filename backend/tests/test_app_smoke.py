from fastapi.testclient import TestClient

from app.main import app
from app.services.recommendation_engine import generate_recommendation


client = TestClient(app)


def test_app_starts():
    assert app is not None
    assert app.title == "AI Career Twin API"


def test_cors_allows_deployed_frontend_and_credentials():
    response = client.options(
        "/health",
        headers={
            "Origin": "https://ai-career-twin-frontend.onrender.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://ai-career-twin-frontend.onrender.com"
    )
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_cors_preserves_localhost_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_registration_rejects_invalid_fields_without_weakening_validation():
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "username": "x",
            "full_name": "A",
            "password": "short",
        },
        headers={"Origin": "https://ai-career-twin-frontend.onrender.com"},
    )

    assert response.status_code == 422
    assert len(response.json()["detail"]) == 4
    assert response.headers["access-control-allow-origin"] == (
        "https://ai-career-twin-frontend.onrender.com"
    )


def test_login_errors_include_cors_headers():
    response = client.post(
        "/auth/login-json",
        json={"username": "missing_user", "password": "wrong-password"},
        headers={"Origin": "https://ai-career-twin-frontend.onrender.com"},
    )

    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == (
        "https://ai-career-twin-frontend.onrender.com"
    )


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
