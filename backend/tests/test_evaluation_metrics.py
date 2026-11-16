from app.models.recommendation import Recommendation
from app.models.skill import RoleSkill, Skill, TargetRole


def test_evaluation_metrics_use_real_recommendation_outcomes(client, db):
    role = TargetRole(name="Back-end Engineer", domain="Engineering", description="Backend role")
    python = Skill(name="Python", category="Programming")
    db.add_all([role, python])
    db.flush()
    db.add(RoleSkill(role_id=role.id, skill_id=python.id, required_level=4.0, importance=5.0))
    db.commit()
    role_id = role.id
    python_id = python.id

    registration = client.post(
        "/auth/register",
        json={"email": "eval@example.com", "username": "eval_user", "full_name": "Eval Candidate", "password": "password123"},
    )
    assert registration.status_code == 200

    login = client.post("/auth/login-json", json={"username": "eval_user", "password": "password123"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    profile = client.put("/candidate/profile", json={"name": "Eval Candidate", "career_goal": "Back-end Engineer"}, headers=headers)
    assert profile.status_code == 200
    assert client.put(f"/roles/{role_id}/select", headers=headers).status_code == 200
    assert client.put("/skills/candidate", json={"skill_id": python_id, "current_level": 2.0, "confidence": 0.8, "evidence": "Practice set"}, headers=headers).status_code == 200

    recommendation = client.post("/recommendations/generate", headers=headers)
    assert recommendation.status_code == 200
    recommendation_id = recommendation.json()["id"]

    assert client.post(f"/recommendations/{recommendation_id}/accept", headers=headers).status_code == 200
    assert client.post(f"/recommendations/{recommendation_id}/complete", headers=headers).status_code == 200
    outcome = client.post(
        f"/recommendations/{recommendation_id}/outcome",
        json={"before_score": 2.0, "after_score": 3.5, "recommendation_followed": True, "completion_status": "evaluated"},
        headers=headers,
    )
    assert outcome.status_code == 200

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    evaluation = dashboard.json()["evaluation"]

    assert evaluation["total_recommendations"] == 2
    assert evaluation["completed_recommendations"] >= 1
    assert evaluation["recommendation_completion_rate"] is not None
    assert evaluation["successful_outcomes"] >= 1
    assert evaluation["average_skill_improvement"] == 1.5
    assert evaluation["identified_skill_gaps"] >= 1
    assert evaluation["skill_improvements"]
    assert evaluation["before_after_skill_levels"][0]["target_skill"] == "Python"
    assert evaluation["before_after_skill_levels"][0]["before_score"] == 2.0
    assert evaluation["before_after_skill_levels"][0]["after_score"] == 3.5

    stored = db.query(Recommendation).count()
    assert stored >= 2
