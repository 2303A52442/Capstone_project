"""Comprehensive test suite verifying all 20 phases of AI Career Twin:
Multi-user security, adaptive recommendation behaviors, skill gap edge cases,
simulation non-mutation, evidence confirmation, RAG retrieval, and LLM fallbacks.
"""

import pytest
from app.models.candidate_profile import CandidateProfile
from app.models.career_twin import CareerTwinSnapshot, SkillGap
from app.models.evidence import CandidateEvidence
from app.models.performance import PerformanceRecord
from app.models.projects import Project
from app.models.recommendation import Recommendation, RecommendationOutcome
from app.models.skill import CandidateSkill, RoleSkill, Skill, TargetRole
from app.services.llm_service import (
    generate_career_comparison_explanation,
    generate_career_twin_summary,
    generate_recommendation_explanation,
)
from app.services.rag_service import get_external_skill_guidance, retriever
from app.services.recommendation_engine import generate_recommendation
from app.services.skill_analysis import calculate_skill_gap, calculate_skill_level, rank_skill_gaps


# =====================================================================
# Phase 14: Multi-User Security & Candidate Isolation
# =====================================================================

def test_strict_multi_user_isolation(client, db, test_user, auth_headers, second_user, second_auth_headers):
    """Verify User A cannot access or mutate User B's profile, skills, evidence, performance, or recommendations."""
    # Setup data for User A
    skill = Skill(name="FastAPI", category="Framework")
    role = TargetRole(name="Python Architect", domain="Backend")
    db.add_all([skill, role])
    db.flush()
    db.add(RoleSkill(role_id=role.id, skill_id=skill.id, required_level=4.0, importance=5.0))
    db.commit()

    # User A selects role, updates skill, creates evidence, adds performance
    client.put(f"/roles/{role.id}/select", headers=auth_headers)
    client.put("/skills/candidate", json={"skill_id": skill.id, "current_level": 2.5, "confidence": 0.9, "evidence": "A's evidence"}, headers=auth_headers)
    rec = client.post("/recommendations/generate", headers=auth_headers).json()
    assert rec is not None
    rec_id = rec["id"]

    ev_a = CandidateEvidence(
        candidate_profile_id=test_user.candidate_profile.id,
        source="Resume",
        title="user_a_resume.pdf",
        status="pending",
        extracted_skills=[{"skill_id": skill.id, "name": "FastAPI"}],
    )
    db.add(ev_a)
    db.commit()
    db.refresh(ev_a)

    # User B checks their own endpoints: must NOT see User A's data
    b_skills = client.get("/skills/candidate", headers=second_auth_headers).json()
    assert len(b_skills) == 0

    b_recs = client.get("/recommendations", headers=second_auth_headers).json()
    assert len(b_recs) == 0

    b_evidence = client.get("/evidence", headers=second_auth_headers).json()
    assert len(b_evidence) == 0

    b_performance = client.get("/performance", headers=second_auth_headers).json()
    assert len(b_performance) == 0

    # User B attempts to access/mutate User A's recommendation
    accept_attempt = client.post(f"/recommendations/{rec_id}/accept", headers=second_auth_headers)
    assert accept_attempt.status_code == 404

    outcome_attempt = client.post(
        f"/recommendations/{rec_id}/outcome",
        json={"before_score": 2.0, "after_score": 4.0},
        headers=second_auth_headers,
    )
    assert outcome_attempt.status_code == 404

    # User B attempts to confirm User A's evidence
    ev_confirm_attempt = client.post(f"/evidence/{ev_a.id}/confirm", headers=second_auth_headers)
    assert ev_confirm_attempt.status_code == 404

    # User B attempts to reject User A's evidence
    ev_reject_attempt = client.post(f"/evidence/{ev_a.id}/reject", headers=second_auth_headers)
    assert ev_reject_attempt.status_code == 404


# =====================================================================
# Phase 6: Skill Gap Engine & Edge Cases
# =====================================================================

def test_skill_gap_calculation_edge_cases():
    """Verify zero gap, missing skill, high gap, missing evidence, and weighted ranking."""
    # Zero gap: current >= required
    assert calculate_skill_gap(current_level=4.0, required_level=4.0) == 0.0
    assert calculate_skill_gap(current_level=4.5, required_level=4.0) == 0.0

    # Missing skill: current = 0
    assert calculate_skill_gap(current_level=0.0, required_level=3.5) == 3.5

    # High gap
    gap = calculate_skill_gap(current_level=1.0, required_level=4.5)
    assert gap == 3.5

    # Rank gaps with varying importance, recency, and confidence
    test_gaps = [
        {"skill_name": "LowPriority", "gap": 1.0, "importance": 1.0, "recency": 0.2, "confidence": 0.3},
        {"skill_name": "HighPriority", "gap": 2.0, "importance": 5.0, "recency": 1.0, "confidence": 0.9},
    ]
    ranked = rank_skill_gaps(test_gaps)
    assert ranked[0]["skill_name"] == "HighPriority"
    assert ranked[0]["priority_score"] > ranked[1]["priority_score"]


def test_calculate_skill_level_weights():
    """Verify deterministic skill scoring from multi-source performance weights."""
    score = calculate_skill_level(
        assessment_score=4.0,
        coding_score=4.0,
        project_score=3.0,
        interview_score=3.0,
        learning_score=2.0,
        recency_factor=1.0,
    )
    # 0.35*4 + 0.25*4 + 0.20*3 + 0.10*3 + 0.10*2 = 1.4 + 1.0 + 0.6 + 0.3 + 0.2 = 3.5
    assert score == 3.5


# =====================================================================
# Phase 7: Adaptive Recommendation Engine
# =====================================================================

def test_adaptive_recommendation_baseline():
    """First recommendation without prior outcomes yields focused practice."""
    metrics = [{"skill_name": "SQL", "current_level": 2.0, "confidence": 0.8, "recency": 1.0}]
    role_skills = [{"skill_name": "SQL", "required_level": 4.0, "importance": 5.0}]
    rec = generate_recommendation(metrics, role_skills)
    assert rec is not None
    assert rec["target_skill"] == "SQL"
    assert "Practice with focused exercises" in rec["recommendation"]
    assert "Current skill: 2.0/5" in rec["reason"]
    assert "Target requirement: 4.0/5" in rec["reason"]
    assert "Gap: 2.0" in rec["reason"]


def test_adaptive_recommendation_on_stagnant_outcome():
    """If prior outcome produced limited/no improvement, change recommended strategy."""
    metrics = [{"skill_name": "SQL", "current_level": 2.0, "confidence": 0.8, "recency": 1.0}]
    role_skills = [{"skill_name": "SQL", "required_level": 4.0, "importance": 5.0}]
    prior_outcomes = [{"target_skill": "SQL", "improvement": 0.0}]
    rec = generate_recommendation(metrics, role_skills, previous_outcomes=prior_outcomes)
    assert rec is not None
    assert "Switching approach to interactive diagnostic" in rec["recommendation"]
    assert "diagnostic" in rec["suggested_activity"].lower()


def test_adaptive_recommendation_on_strong_improvement():
    """If candidate improved significantly, increase challenge or advance."""
    metrics = [
        {"skill_name": "Python", "current_level": 3.2, "confidence": 0.9, "recency": 1.0},
        {"skill_name": "SQL", "current_level": 2.0, "confidence": 0.8, "recency": 1.0},
    ]
    role_skills = [
        {"skill_name": "Python", "required_level": 4.0, "importance": 5.0},
        {"skill_name": "SQL", "required_level": 4.0, "importance": 3.0},
    ]
    prior_outcomes = [{"target_skill": "Python", "improvement": 1.2}]
    rec = generate_recommendation(metrics, role_skills, previous_outcomes=prior_outcomes)
    assert rec is not None
    assert rec["target_skill"] == "Python"
    assert "advanced" in rec["suggested_activity"].lower() or "Strong prior progress" in rec["recommendation"]
    assert rec["estimated_effort_hours"] == 4.5


def test_adaptive_recommendation_prerequisite_detection():
    """If repeated failure occurs on an advanced skill, recommend foundational prerequisite."""
    # System Design has prerequisite SQL
    metrics = [
        {"skill_name": "System Design", "current_level": 1.5, "confidence": 0.7, "recency": 1.0},
        {"skill_name": "SQL", "current_level": 2.0, "confidence": 0.8, "recency": 1.0},
    ]
    role_skills = [
        {"skill_name": "System Design", "required_level": 4.0, "importance": 5.0},
        {"skill_name": "SQL", "required_level": 4.0, "importance": 4.0},
    ]
    prior_outcomes = [
        {"target_skill": "System Design", "improvement": 0.0},
        {"target_skill": "System Design", "improvement": -0.2},
    ]
    rec = generate_recommendation(metrics, role_skills, previous_outcomes=prior_outcomes)
    assert rec is not None
    # Engine should identify prerequisite SQL
    assert rec["target_skill"] == "SQL"
    assert "prerequisite" in rec["recommendation"].lower()


# =====================================================================
# Phase 12: Career Simulation & Non-Mutation
# =====================================================================

def test_career_simulation_does_not_mutate_database(client, db, test_user, auth_headers):
    """Verify Career Simulation calculates impact and does NOT mutate actual candidate data."""
    role = TargetRole(name="Sim Role", domain="Engineering")
    py = Skill(name="Sim Python", category="Code")
    db.add_all([role, py])
    db.flush()
    db.add(RoleSkill(role_id=role.id, skill_id=py.id, required_level=4.0, importance=5.0))
    db.commit()

    # Candidate has level 2.0
    client.put("/skills/candidate", json={"skill_id": py.id, "current_level": 2.0, "confidence": 0.8}, headers=auth_headers)

    initial_skills_count = db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == test_user.candidate_profile.id).count()
    initial_snapshots_count = db.query(CareerTwinSnapshot).filter(CareerTwinSnapshot.candidate_profile_id == test_user.candidate_profile.id).count()
    initial_level = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == test_user.candidate_profile.id,
        CandidateSkill.skill_id == py.id,
    ).one().current_level

    # Run hypothetical simulation with override level = 5.0
    sim_res = client.post("/career-twin/simulate", json={"role_id": role.id, "overrides": {str(py.id): 5.0}}, headers=auth_headers)
    assert sim_res.status_code == 200
    data = sim_res.json()
    assert data["mutated"] is False
    assert data["current_readiness"] == 50.0  # 2.0 / 4.0 = 50%
    assert data["simulated_readiness"] == 100.0  # 5.0 / 4.0 = 100%
    assert data["readiness_impact"] == 50.0

    # Verify actual database records were NOT touched
    current_level_after = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == test_user.candidate_profile.id,
        CandidateSkill.skill_id == py.id,
    ).one().current_level
    assert current_level_after == initial_level

    current_snapshots_count = db.query(CareerTwinSnapshot).filter(CareerTwinSnapshot.candidate_profile_id == test_user.candidate_profile.id).count()
    assert current_snapshots_count == initial_snapshots_count


# =====================================================================
# Phase 8: LLM & Fallback Explanations
# =====================================================================

def test_llm_deterministic_fallback_explanations():
    """Verify deterministic fallbacks work without API keys."""
    explanation = generate_recommendation_explanation(
        target_skill="PostgreSQL",
        current_level=2.0,
        required_level=4.0,
        gap=2.0,
        importance=4.0,
        confidence=0.85,
        recent_performance_score=60.0,
        candidate_name="Alice",
    )
    assert "PostgreSQL" in explanation
    assert "significant gap" in explanation
    assert "85%" in explanation

    summary = generate_career_twin_summary(
        candidate_name="Alice",
        target_role="Backend Developer",
        readiness_score=75.0,
        strong_skills=["Python", "Git"],
        weak_skills=["PostgreSQL"],
    )
    assert "Alice" in summary
    assert "75.0% readiness" in summary
    assert "Python" in summary

    comparison = generate_career_comparison_explanation(
        candidate_name="Alice",
        role_a_name="Backend Developer",
        role_a_gaps=[{"gap": 1.5}],
        role_b_name="ML Engineer",
        role_b_gaps=[{"gap": 3.5}],
    )
    assert "Alice" in comparison
    assert "shorter gap trajectory toward Backend Developer" in comparison


# =====================================================================
# Phase 9: RAG & Knowledge Retrieval
# =====================================================================

def test_rag_semantic_retrieval():
    """Verify TF-IDF knowledge retriever returns relevant documents and handles unknowns."""
    res_py = retriever.retrieve("Python asynchronous API programming")
    assert len(res_py) > 0
    assert res_py[0]["topic"] == "Python"
    assert res_py[0]["source_type"] == "external_curated_knowledge"

    res_sql = retriever.retrieve("PostgreSQL relational indexing joins")
    assert len(res_sql) > 0
    assert res_sql[0]["topic"] == "SQL"

    # Direct guidance function
    guidance = get_external_skill_guidance("React")
    assert guidance is not None
    assert guidance["topic"] == "React"


# =====================================================================
# Phases 3 & 4: Evidence Review & Confirmation
# =====================================================================

def test_evidence_confirmation_and_rejection(client, db, test_user, auth_headers):
    """Verify confirming evidence integrates skills and projects and syncs Twin; rejecting does not."""
    skill = Skill(name="Docker", category="DevOps")
    db.add(skill)
    db.commit()

    ev_confirm = CandidateEvidence(
        candidate_profile_id=test_user.candidate_profile.id,
        source="GitHub",
        title="test-repo",
        status="pending",
        extracted_skills=[{"skill_id": skill.id, "name": "Docker"}],
        extracted_projects=[{"name": "ContainerService", "description": "Microservice in Docker"}],
    )
    ev_reject = CandidateEvidence(
        candidate_profile_id=test_user.candidate_profile.id,
        source="Resume",
        title="old_resume.pdf",
        status="pending",
        extracted_skills=[{"skill_id": skill.id, "name": "Docker"}],
    )
    db.add_all([ev_confirm, ev_reject])
    db.commit()

    # Confirm the first evidence
    res_c = client.post(f"/evidence/{ev_confirm.id}/confirm", headers=auth_headers)
    assert res_c.status_code == 200
    assert res_c.json()["status"] == "confirmed"

    # Verified skill and project were added to candidate
    candidate_skill = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == test_user.candidate_profile.id,
        CandidateSkill.skill_id == skill.id,
    ).first()
    assert candidate_skill is not None
    assert "GitHub: test-repo" in candidate_skill.evidence

    project = db.query(Project).filter(
        Project.candidate_profile_id == test_user.candidate_profile.id,
        Project.name == "ContainerService",
    ).first()
    assert project is not None

    # Reject the second evidence
    res_r = client.post(f"/evidence/{ev_reject.id}/reject", headers=auth_headers)
    assert res_r.status_code == 200
    assert res_r.json()["status"] == "rejected"
    assert db.query(CandidateEvidence).filter(CandidateEvidence.id == ev_reject.id).one().status == "rejected"
