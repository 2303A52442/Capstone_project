from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.performance import PerformanceRecord
from app.models.recommendation import Recommendation, RecommendationOutcome
from app.models.skill import CandidateSkill, CandidateTargetRole, RoleSkill
from app.services.skill_analysis import calculate_skill_gap, rank_skill_gaps
from app.services.evaluation import calculate_evaluation_metrics
from app.models.user import User

router = APIRouter()


@router.get("")
def dashboard_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    candidate_skills = {
        skill.skill_id: skill
        for skill in db.query(CandidateSkill).filter(
            CandidateSkill.candidate_profile_id == profile.id,
        ).all()
    }
    target = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    role_skills = []
    if target:
        role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == target.role_id).all()

    gaps = []
    for role_skill in role_skills:
        candidate_skill = candidate_skills.get(role_skill.skill_id)
        current_level = candidate_skill.current_level if candidate_skill else 0.0
        gaps.append({
            "skill_name": role_skill.skill.name,
            "current_level": current_level,
            "required_level": role_skill.required_level,
            "gap": calculate_skill_gap(current_level, role_skill.required_level),
            "importance": role_skill.importance,
            "confidence": candidate_skill.confidence if candidate_skill else 0.0,
            "recency": 1.0 if candidate_skill else 0.0,
        })

    ranked_gaps = rank_skill_gaps(gaps)
    strong_skills = [
        skill.skill.name
        for skill in candidate_skills.values()
        if skill.current_level >= 3.5
    ]
    readiness = 0.0
    if role_skills:
        readiness = sum(
            min(candidate_skills.get(role_skill.skill_id).current_level if candidate_skills.get(role_skill.skill_id) else 0.0,
                role_skill.required_level) / role_skill.required_level
            if role_skill.required_level else 1.0
            for role_skill in role_skills
        ) / len(role_skills)

    recommendation_count = db.query(Recommendation).filter(
        Recommendation.candidate_profile_id == profile.id,
        Recommendation.status.in_(["generated", "accepted"]),
    ).count()
    recent_performance = db.query(PerformanceRecord).filter(
        PerformanceRecord.candidate_profile_id == profile.id,
    ).order_by(PerformanceRecord.recorded_at.desc()).limit(5).all()
    outcome_count = db.query(RecommendationOutcome).join(Recommendation).filter(
        Recommendation.candidate_profile_id == profile.id,
    ).count()
    all_recommendations = db.query(Recommendation).filter(Recommendation.candidate_profile_id == profile.id).all()
    outcomes = db.query(RecommendationOutcome).join(Recommendation).filter(Recommendation.candidate_profile_id == profile.id).all()

    from app.models.evidence import CandidateEvidence

    completed_actions = db.query(Recommendation).filter(
        Recommendation.candidate_profile_id == profile.id,
        Recommendation.status.in_(["completed", "evaluated"]),
    ).count()

    evidence_sources = [
        row[0] for row in db.query(CandidateEvidence.source).filter(
            CandidateEvidence.candidate_profile_id == profile.id
        ).distinct().all()
    ]

    return {
        "candidate": profile.name,
        "career_goal": profile.career_goal,
        "target_role": target.target_role.name if target and target.target_role else None,
        "readiness_indicator": "Strong" if readiness >= 0.8 else "Developing" if readiness >= 0.5 else "Early",
        "readiness_score": round(readiness * 100, 1),
        "strong_skills": strong_skills,
        "weak_skills": [gap["skill_name"] for gap in ranked_gaps if gap["gap"] > 0],
        "top_skill_gaps": [gap["skill_name"] for gap in ranked_gaps[:3] if gap["gap"] > 0],
        "skill_snapshot": [
            {
                "name": role_skill.skill.name,
                "value": round(
                    min(
                        candidate_skills.get(role_skill.skill_id).current_level
                        if candidate_skills.get(role_skill.skill_id)
                        else 0.0,
                        role_skill.required_level,
                    ) / role_skill.required_level * 100,
                    1,
                ) if role_skill.required_level else 0.0,
            }
            for role_skill in role_skills
        ],
        "current_recommendations": recommendation_count,
        "completed_actions": completed_actions,
        "evidence_sources": evidence_sources,
        "recent_performance": [
            {
                "id": record.id,
                "record_type": record.record_type,
                "topic": record.topic,
                "score": record.score,
                "recorded_at": record.recorded_at,
            }
            for record in recent_performance
        ],
        "outcome_count": outcome_count,
        "evaluation": calculate_evaluation_metrics(all_recommendations, outcomes, gaps, role_skills),
    }
