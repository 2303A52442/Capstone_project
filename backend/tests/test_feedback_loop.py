from app.models.career_twin import CareerTwinSnapshot, SkillGap
from app.models.recommendation import Recommendation, RecommendationExplanation
from app.models.skill import CandidateSkill, RoleSkill, Skill, TargetRole


def test_candidate_feedback_loop_from_profile_to_outcome(client, db):
    role = TargetRole(name="Backend Developer", domain="Engineering", description="Backend role")
    comparison_role = TargetRole(name="Data Analyst", domain="Analytics", description="Analytics role")
    python = Skill(name="Python", category="Programming")
    system_design = Skill(name="System Design", category="Architecture")
    db.add_all([role, comparison_role, python, system_design])
    db.flush()
    db.add_all([
        RoleSkill(role_id=role.id, skill_id=python.id, required_level=4.0, importance=5.0),
        RoleSkill(role_id=role.id, skill_id=system_design.id, required_level=4.0, importance=3.0),
        RoleSkill(role_id=comparison_role.id, skill_id=python.id, required_level=3.0, importance=3.0),
    ])
    db.commit()
    role_id = role.id
    comparison_role_id = comparison_role.id
    python_id = python.id

    registration = client.post("/auth/register", json={
        "email": "loop@example.com",
        "username": "loop_user",
        "full_name": "Loop Candidate",
        "password": "password123",
    })
    assert registration.status_code == 200

    login = client.post("/auth/login-json", json={
        "username": "loop_user",
        "password": "password123",
    })
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    profile = client.put("/candidate/profile", json={
        "name": "Loop Candidate",
        "career_goal": "Backend Developer",
    }, headers=headers)
    assert profile.status_code == 200

    selection = client.put(f"/roles/{role_id}/select", headers=headers)
    assert selection.status_code == 200

    skill_update = client.put("/skills/candidate", json={
        "skill_id": python_id,
        "current_level": 2.0,
        "confidence": 0.8,
        "evidence": "Completed API implementation exercises",
    }, headers=headers)
    assert skill_update.status_code == 200

    performance = client.post("/performance", json={
        "record_type": "assessment",
        "topic": "Python APIs assessment",
        "score": 58,
        "score_percent": 58,
        "skill_focus": "Python",
        "total_questions": 20,
        "correct_answers": 12,
    }, headers=headers)
    assert performance.status_code == 200

    recommendation = client.post("/recommendations/generate", headers=headers)
    assert recommendation.status_code == 200
    recommendation_id = recommendation.json()["id"]
    assert recommendation.json()["target_skill"] == "Python"

    assert client.post(f"/recommendations/{recommendation_id}/accept", headers=headers).status_code == 200
    assert client.post(f"/recommendations/{recommendation_id}/complete", headers=headers).status_code == 200
    outcome = client.post(f"/recommendations/{recommendation_id}/outcome", json={
        "before_score": 2.0,
        "after_score": 3.5,
        "recommendation_followed": True,
        "completion_status": "evaluated",
    }, headers=headers)
    assert outcome.status_code == 200
    outcome_data = outcome.json()
    assert outcome_data["updated_skill"]["previous_level"] == 2.0
    assert outcome_data["updated_skill"]["current_level"] == 3.5
    assert outcome_data["next_recommendation_id"] is not None

    career_twin = client.get("/career-twin", headers=headers)
    assert career_twin.status_code == 200
    assert career_twin.json()["target_role"] == "Backend Developer"
    assert career_twin.json()["history"]

    comparison = client.get(f"/comparison?role_a_id={role_id}&role_b_id={comparison_role_id}", headers=headers)
    assert comparison.status_code == 200
    assert comparison.json()["role_a"]["name"] == "Backend Developer"
    assert comparison.json()["role_b"]["name"] == "Data Analyst"

    simulation = client.post("/career-twin/simulate", json={"role_id": role_id, "overrides": {str(python_id): 4.5}}, headers=headers)
    assert simulation.status_code == 200
    assert simulation.json()["mutated"] is False
    assert "Python" in simulation.json()["affected_skills"]

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["readiness_score"] >= 0

    stored = db.query(Recommendation).filter(Recommendation.id == recommendation_id).one()
    assert stored.status == "evaluated"
    updated_skill = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == profile.json()["id"],
        CandidateSkill.skill_id == python_id,
    ).one()
    assert updated_skill.current_level == 3.5
    assert db.query(SkillGap).filter(SkillGap.candidate_profile_id == profile.json()["id"]).count() == 2
    assert db.query(CareerTwinSnapshot).filter(CareerTwinSnapshot.candidate_profile_id == profile.json()["id"]).count() >= 1
    assert db.query(Recommendation).filter(
        Recommendation.candidate_profile_id == profile.json()["id"],
        Recommendation.status == "generated",
    ).count() == 1


def test_candidate_data_isolation_between_users(client, db):
    skill = Skill(name="Python", category="Programming")
    db.add(skill)
    db.commit()
    skill_id = skill.id

    first = client.post("/auth/register", json={
        "email": "first@example.com",
        "username": "first_user",
        "full_name": "First Candidate",
        "password": "password123",
    })
    second = client.post("/auth/register", json={
        "email": "second@example.com",
        "username": "second_user",
        "full_name": "Second Candidate",
        "password": "password123",
    })
    assert first.status_code == 200
    assert second.status_code == 200

    first_login = client.post("/auth/login-json", json={"username": "first_user", "password": "password123"})
    first_headers = {"Authorization": f"Bearer {first_login.json()['access_token']}"}
    first_profile = client.put("/candidate/profile", json={"name": "First Candidate", "career_goal": "Developer"}, headers=first_headers)
    assert first_profile.status_code == 200
    assert client.put("/skills/candidate", json={"skill_id": skill_id, "current_level": 4, "confidence": 1, "evidence": "First candidate evidence"}, headers=first_headers).status_code == 200

    second_login = client.post("/auth/login-json", json={"username": "second_user", "password": "password123"})
    second_headers = {"Authorization": f"Bearer {second_login.json()['access_token']}"}
    second_profile = client.put("/candidate/profile", json={"name": "Second Candidate", "career_goal": "Developer"}, headers=second_headers)
    assert second_profile.status_code == 200
    assert client.get("/skills/candidate", headers=second_headers).json() == []
    assert client.get("/recommendations", headers=second_headers).json() == []
    assert client.get("/evidence", headers=second_headers).json() == []

    first_skill = db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == first_profile.json()["id"]).one()
    assert first_skill.evidence == "First candidate evidence"
    assert first_skill.current_level == 4


def test_recommendation_includes_generated_explanation(client, db):
    role = TargetRole(name="Backend Developer", domain="Engineering", description="Backend role")
    python = Skill(name="Python", category="Programming")
    db.add_all([role, python])
    db.flush()
    db.add(RoleSkill(role_id=role.id, skill_id=python.id, required_level=4.0, importance=5.0))
    db.commit()
    role_id = role.id
    python_id = python.id

    registration = client.post("/auth/register", json={"email": "llm@example.com", "username": "llm_user", "full_name": "LLM Candidate", "password": "password123"})
    assert registration.status_code == 200

    login = client.post("/auth/login-json", json={"username": "llm_user", "password": "password123"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    profile = client.put("/candidate/profile", json={"name": "LLM Candidate", "career_goal": "Backend Developer"}, headers=headers)
    assert profile.status_code == 200

    assert client.put(f"/roles/{role_id}/select", headers=headers).status_code == 200
    assert client.put("/skills/candidate", json={"skill_id": python_id, "current_level": 2.0, "confidence": 0.8, "evidence": "Basic exercises"}, headers=headers).status_code == 200

    recommendation = client.post("/recommendations/generate", headers=headers)
    assert recommendation.status_code == 200
    rec_data = recommendation.json()
    recommendation_id = rec_data["id"]

    explanation = db.query(RecommendationExplanation).filter(RecommendationExplanation.recommendation_id == recommendation_id).first()
    assert explanation is not None
    assert len(explanation.explanation) > 0
    assert "Python" in explanation.explanation or "skill" in explanation.explanation.lower()
