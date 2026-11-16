from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.career_twin import CandidateEvent, CareerTwinSnapshot, SkillGap
from app.models.performance import PerformanceRecord
from app.models.recommendation import Recommendation, RecommendationOutcome
from app.models.skill import CandidateSkill, CandidateTargetRole, RoleSkill
from app.services.skill_analysis import calculate_skill_gap
from app.services.evaluation import calculate_evaluation_metrics
from app.models.user import User

router = APIRouter()


@router.post("/simulate")
def simulate_skill_changes(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    target = db.query(CandidateTargetRole).filter(CandidateTargetRole.candidate_profile_id == profile.id).first()
    role_id = payload.get("role_id") or (target.role_id if target else None)
    if not role_id:
        raise HTTPException(status_code=400, detail="Select a role or provide role_id")

    candidate_levels = {
        str(skill.skill_id): float(skill.current_level)
        for skill in db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == profile.id).all()
    }
    overrides = {str(key): float(value) for key, value in payload.get("overrides", {}).items()}
    current = []
    simulated = []
    for role_skill in db.query(RoleSkill).filter(RoleSkill.role_id == role_id).all():
        current_level = candidate_levels.get(str(role_skill.skill_id), 0.0)
        simulated_level = overrides.get(str(role_skill.skill_id), current_level)
        current.append({"skill_id": role_skill.skill_id, "skill_name": role_skill.skill.name, "current_level": current_level, "required_level": role_skill.required_level, "gap": calculate_skill_gap(current_level, role_skill.required_level)})
        simulated.append({"skill_id": role_skill.skill_id, "skill_name": role_skill.skill.name, "current_level": simulated_level, "required_level": role_skill.required_level, "gap": calculate_skill_gap(simulated_level, role_skill.required_level)})
    current_map = {item["skill_name"]: item["gap"] for item in current}
    current_readiness = round(
        sum(min(item["current_level"], item["required_level"]) / item["required_level"] if item["required_level"] else 1.0 for item in current) / len(current) * 100, 1
    ) if current else 0.0
    simulated_readiness = round(
        sum(min(item["current_level"], item["required_level"]) / item["required_level"] if item["required_level"] else 1.0 for item in simulated) / len(simulated) * 100, 1
    ) if simulated else 0.0

    return {
        "role_id": role_id,
        "mutated": False,
        "current_readiness": current_readiness,
        "simulated_readiness": simulated_readiness,
        "readiness_impact": round(simulated_readiness - current_readiness, 1),
        "current": current,
        "simulated": simulated,
        "affected_skills": [item["skill_name"] for item in simulated if item["gap"] != current_map[item["skill_name"]]],
    }


@router.get("")
def get_career_twin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    target = db.query(CandidateTargetRole).filter(CandidateTargetRole.candidate_profile_id == profile.id).first()
    skills = db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == profile.id).all()
    recommendations = db.query(Recommendation).filter(Recommendation.candidate_profile_id == profile.id).order_by(Recommendation.created_at.desc()).all()
    outcomes = db.query(RecommendationOutcome).join(Recommendation).filter(Recommendation.candidate_profile_id == profile.id).order_by(RecommendationOutcome.recorded_at.desc()).all()
    snapshots = db.query(CareerTwinSnapshot).filter(CareerTwinSnapshot.candidate_profile_id == profile.id).order_by(CareerTwinSnapshot.created_at.desc()).all()
    gaps = db.query(SkillGap).filter(SkillGap.candidate_profile_id == profile.id).order_by(SkillGap.priority.desc()).all()
    role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == target.role_id).all() if target else []
    strong_skills = [skill.skill.name for skill in skills if skill.current_level >= 3.5]
    weak_skills = [skill.skill.name for skill in skills if skill.current_level < 3.5]
    readiness = snapshots[0].readiness_score if snapshots else None

    from app.services.llm_service import generate_career_twin_summary
    from app.models.evidence import CandidateEvidence

    evidence_sources = [
        row[0] for row in db.query(CandidateEvidence.source).filter(
            CandidateEvidence.candidate_profile_id == profile.id
        ).distinct().all()
    ]

    summary_narrative = generate_career_twin_summary(
        candidate_name=profile.name,
        target_role=target.target_role.name if target else None,
        readiness_score=readiness or 0.0,
        strong_skills=strong_skills,
        weak_skills=weak_skills,
    )

    return {
        "candidate": profile.name,
        "career_goal": profile.career_goal,
        "profile_id": profile.id,
        "target_role": target.target_role.name if target else None,
        "readiness_score": readiness,
        "summary_narrative": summary_narrative,
        "evidence_sources": evidence_sources,
        "strong_skills": strong_skills,
        "weak_skills": weak_skills,
        "skills": [{
            "name": skill.skill.name,
            "category": skill.skill.category,
            "current_level": skill.current_level,
            "confidence": skill.confidence,
            "evidence": skill.evidence,
        } for skill in skills],
        "skill_gaps": [{
            "skill_name": gap.skill_name,
            "current_level": gap.current_level,
            "required_level": gap.required_level,
            "gap": gap.gap,
            "priority": gap.priority,
            "evidence": gap.evidence,
        } for gap in gaps],
        "performance": [{
            "record_type": record.record_type,
            "topic": record.topic,
            "score": record.score,
            "recorded_at": record.recorded_at,
        } for record in db.query(PerformanceRecord).filter(PerformanceRecord.candidate_profile_id == profile.id).order_by(PerformanceRecord.recorded_at.desc()).all()],
        "recommendations": [{
            "id": item.id,
            "target_skill": item.target_skill,
            "status": item.status,
            "recommendation_text": item.recommendation_text,
            "created_at": item.created_at,
        } for item in recommendations],
        "outcomes": [{
            "recommendation_id": item.recommendation_id,
            "before_score": item.before_score,
            "after_score": item.after_score,
            "improvement": item.improvement,
            "recorded_at": item.recorded_at,
        } for item in outcomes],
        "history": [{
            "summary": item.summary,
            "readiness_score": item.readiness_score,
            "strong_skills": item.strong_skills,
            "weak_skills": item.weak_skills,
            "created_at": item.created_at,
        } for item in snapshots],
        "events": [{
            "event_type": item.event_type,
            "description": item.description,
            "created_at": item.created_at,
        } for item in db.query(CandidateEvent).filter(CandidateEvent.candidate_profile_id == profile.id).order_by(CandidateEvent.created_at.desc()).all()],
        "evaluation": calculate_evaluation_metrics(recommendations, outcomes, gaps, role_skills),
    }


@router.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"history": db.query(CareerTwinSnapshot).filter(CareerTwinSnapshot.candidate_profile_id == profile.id).order_by(CareerTwinSnapshot.created_at.desc()).all()}


@router.get("/skill-gaps")
def get_skill_gaps(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    gaps = db.query(SkillGap).filter(SkillGap.candidate_profile_id == profile.id).all()
    return [{
        "skill_name": gap.skill_name,
        "current_level": gap.current_level,
        "required_level": gap.required_level,
        "gap": gap.gap,
        "priority": gap.priority,
    } for gap in gaps]
