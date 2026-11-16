from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.recommendation import Recommendation, RecommendationOutcome, RecommendationExplanation
from app.models.skill import CandidateSkill, CandidateTargetRole, RoleSkill
from app.services.recommendation_engine import generate_recommendation
from app.models.user import User
from app.services.career_twin_service import refresh_candidate_state
from app.services.llm_service import generate_recommendation_explanation
from app.schemas.recommendation import RecommendationRead

router = APIRouter()


def _candidate_profile(current_user: User, db: Session) -> CandidateProfile:
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


from typing import Optional
from app.models.performance import PerformanceRecord


@router.get("", response_model=list[RecommendationRead])
def list_recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _candidate_profile(current_user, db)
    recs = db.query(Recommendation).filter(Recommendation.candidate_profile_id == profile.id).order_by(Recommendation.created_at.desc()).all()
    explanation_map = {
        exp.recommendation_id: exp.explanation
        for exp in db.query(RecommendationExplanation).filter(
            RecommendationExplanation.recommendation_id.in_([r.id for r in recs])
        ).all()
    } if recs else {}
    for r in recs:
        r.explanation = explanation_map.get(r.id)
    return recs


@router.post("/generate", response_model=Optional[RecommendationRead])
def generate_candidate_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _candidate_profile(current_user, db)
    target = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    if not target:
        raise HTTPException(status_code=400, detail="Select a target role before generating recommendations")

    candidate_metrics = [
        {
            "skill_name": skill.skill.name,
            "current_level": skill.current_level,
            "confidence": skill.confidence,
            "recency": 1.0,
        }
        for skill in db.query(CandidateSkill).filter(
            CandidateSkill.candidate_profile_id == profile.id,
        ).all()
    ]
    role_skills = [
        {
            "skill_name": role_skill.skill.name,
            "required_level": role_skill.required_level,
            "importance": role_skill.importance,
        }
        for role_skill in db.query(RoleSkill).filter(RoleSkill.role_id == target.role_id).all()
    ]
    previous_outcomes = [
        {"target_skill": recommendation.target_skill, "improvement": outcome.improvement}
        for recommendation, outcome in db.query(Recommendation, RecommendationOutcome).join(
            RecommendationOutcome, RecommendationOutcome.recommendation_id == Recommendation.id,
        ).filter(Recommendation.candidate_profile_id == profile.id).order_by(RecommendationOutcome.recorded_at.asc()).all()
    ]
    recent_perf = [
        {"topic": p.topic, "score": p.score, "record_type": p.record_type}
        for p in db.query(PerformanceRecord).filter(PerformanceRecord.candidate_profile_id == profile.id).order_by(PerformanceRecord.recorded_at.desc()).limit(10).all()
    ]
    recommendation_data = generate_recommendation(
        candidate_metrics, role_skills, previous_outcomes, recent_performance=recent_perf
    )
    if not recommendation_data:
        return None

    recommendation = Recommendation(
        candidate_profile_id=profile.id,
        target_skill=recommendation_data["target_skill"],
        recommendation_text=recommendation_data["recommendation"],
        reason=recommendation_data["reason"],
        priority=2 if recommendation_data["priority"] == "High" else 1,
        expected_outcome=recommendation_data["expected_outcome"],
        suggested_activity=recommendation_data["suggested_activity"],
        estimated_effort_hours=recommendation_data["estimated_effort_hours"],
        success_metric=recommendation_data["success_metric"],
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    matching_perf = next((p["score"] for p in recent_perf if recommendation_data["target_skill"].lower() in str(p.get("topic", "")).lower()), None)
    last_outcome_val = next((o["improvement"] for o in reversed(previous_outcomes) if o["target_skill"] == recommendation_data["target_skill"]), None)

    explanation_text = generate_recommendation_explanation(
        target_skill=recommendation_data["target_skill"],
        current_level=recommendation_data.get("current_level", 0),
        required_level=recommendation_data.get("required_level", 0),
        gap=recommendation_data.get("gap", 0),
        importance=recommendation_data.get("importance", 1),
        confidence=recommendation_data.get("confidence", 0.5),
        recent_performance_score=matching_perf,
        previous_improvement=last_outcome_val,
        candidate_name=profile.name,
    )
    explanation = RecommendationExplanation(
        recommendation_id=recommendation.id,
        explanation=explanation_text,
    )
    db.add(explanation)
    db.commit()
    db.refresh(explanation)

    recommendation.explanation = explanation_text
    return recommendation


@router.post("/{recommendation_id}/accept")
def accept_recommendation(recommendation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _candidate_profile(current_user, db)
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.candidate_profile_id == profile.id,
    ).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    recommendation.status = "accepted"
    db.commit()
    return {"status": "accepted", "recommendation_id": recommendation.id}


@router.post("/{recommendation_id}/complete")
def complete_recommendation(recommendation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _candidate_profile(current_user, db)
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.candidate_profile_id == profile.id,
    ).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    recommendation.status = "completed"
    db.commit()
    return {"status": "completed", "recommendation_id": recommendation.id}


@router.post("/{recommendation_id}/outcome")
def record_outcome(recommendation_id: int, payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _candidate_profile(current_user, db)
    recommendation = db.query(Recommendation).filter(
        Recommendation.id == recommendation_id,
        Recommendation.candidate_profile_id == profile.id,
    ).first()
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    outcome = RecommendationOutcome(
        recommendation_id=recommendation.id,
        accepted=True,
        completed=True,
        recommendation_followed=payload.get("recommendation_followed", True),
        before_score=payload.get("before_score", 0),
        after_score=payload.get("after_score", 0),
        improvement=payload.get("after_score", 0) - payload.get("before_score", 0),
        completion_status=payload.get("completion_status", "evaluated"),
        time_taken_hours=payload.get("time_taken_hours"),
        outcome_notes=payload.get("outcome_notes"),
    )
    db.add(outcome)
    recommendation.status = "evaluated"
    try:
        state = refresh_candidate_state(
            db=db,
            profile=profile,
            target_skill=recommendation.target_skill,
            before_score=payload.get("before_score", 0),
            after_score=payload.get("after_score", 0),
            outcome_notes=payload.get("outcome_notes"),
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error)) from error

    target = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    refreshed_metrics = [
        {
            "skill_name": skill.skill.name,
            "current_level": skill.current_level,
            "confidence": skill.confidence,
            "recency": 1.0,
        }
        for skill in db.query(CandidateSkill).filter(
            CandidateSkill.candidate_profile_id == profile.id,
        ).all()
    ]
    target_role_skills = [
        {
            "skill_name": role_skill.skill.name,
            "required_level": role_skill.required_level,
            "importance": role_skill.importance,
        }
        for role_skill in db.query(RoleSkill).filter(RoleSkill.role_id == target.role_id).all()
    ]
    previous_outcomes = [
        {"target_skill": prior.target_skill, "improvement": result.improvement}
        for prior, result in db.query(Recommendation, RecommendationOutcome).join(
            RecommendationOutcome, RecommendationOutcome.recommendation_id == Recommendation.id,
        ).filter(Recommendation.candidate_profile_id == profile.id).order_by(RecommendationOutcome.recorded_at.asc()).all()
    ]
    recent_perf = [
        {"topic": p.topic, "score": p.score, "record_type": p.record_type}
        for p in db.query(PerformanceRecord).filter(PerformanceRecord.candidate_profile_id == profile.id).order_by(PerformanceRecord.recorded_at.desc()).limit(10).all()
    ]
    next_data = generate_recommendation(refreshed_metrics, target_role_skills, previous_outcomes, recent_performance=recent_perf)
    next_recommendation = None
    if next_data:
        next_recommendation = Recommendation(
            candidate_profile_id=profile.id,
            target_skill=next_data["target_skill"],
            recommendation_text=next_data["recommendation"],
            reason=next_data["reason"],
            priority=2 if next_data["priority"] == "High" else 1,
            expected_outcome=next_data["expected_outcome"],
            suggested_activity=next_data["suggested_activity"],
            estimated_effort_hours=next_data["estimated_effort_hours"],
            success_metric=next_data["success_metric"],
        )
        db.add(next_recommendation)
        db.commit()
        db.refresh(next_recommendation)

        matching_perf = next((p["score"] for p in recent_perf if next_data["target_skill"].lower() in str(p.get("topic", "")).lower()), None)
        last_outcome_val = next((o["improvement"] for o in reversed(previous_outcomes) if o["target_skill"] == next_data["target_skill"]), None)

        next_explanation = generate_recommendation_explanation(
            target_skill=next_data["target_skill"],
            current_level=next_data.get("current_level", 0),
            required_level=next_data.get("required_level", 0),
            gap=next_data.get("gap", 0),
            importance=next_data.get("importance", 1),
            confidence=next_data.get("confidence", 0.5),
            recent_performance_score=matching_perf,
            previous_improvement=last_outcome_val,
            candidate_name=profile.name,
        )
        db.add(RecommendationExplanation(recommendation_id=next_recommendation.id, explanation=next_explanation))

    db.commit()
    if next_recommendation:
        db.refresh(next_recommendation)
    return {
        "status": "recorded",
        "recommendation_id": recommendation.id,
        "outcome_id": outcome.id,
        "updated_skill": state,
        "next_recommendation_id": next_recommendation.id if next_recommendation else None,
    }
