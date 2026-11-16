from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.skill import CandidateSkill, Skill
from app.models.user import User
from app.schemas.skill import CandidateSkillUpdate, SkillCreate, SkillRead

router = APIRouter()


@router.get("", response_model=list[SkillRead])
def list_skills(db: Session = Depends(get_db)):
    return db.query(Skill).all()


@router.post("", response_model=SkillRead)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Skill).filter(Skill.name == payload.name).first()
    if existing:
        return existing

    skill = Skill(**payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/candidate", response_model=list[dict])
def list_candidate_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.candidate_profile import CandidateProfile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return [
        {
            "id": skill.id,
            "skill_id": skill.skill_id,
            "name": skill.skill.name,
            "current_level": skill.current_level,
            "confidence": skill.confidence,
            "evidence": skill.evidence,
        }
        for skill in db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == profile.id).all()
    ]


@router.put("/candidate")
def upsert_candidate_skill(payload: CandidateSkillUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.candidate_profile import CandidateProfile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    candidate_skill = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == profile.id,
        CandidateSkill.skill_id == payload.skill_id,
    ).first()

    if candidate_skill is None:
        candidate_skill = CandidateSkill(
            candidate_profile_id=profile.id,
            skill_id=payload.skill_id,
        )
        db.add(candidate_skill)

    candidate_skill.current_level = payload.current_level
    candidate_skill.confidence = payload.confidence
    candidate_skill.evidence = payload.evidence
    db.flush()

    from app.services.career_twin_service import sync_career_twin_state
    sync_career_twin_state(
        db=db,
        profile=profile,
        summary=f"Skill updated: {candidate_skill.skill.name if candidate_skill.skill else 'Skill'} set to {payload.current_level}/5.",
        event_type="skill_updated",
        event_description=f"Candidate skill level updated to {payload.current_level} with confidence {payload.confidence}.",
    )
    db.commit()
    return {"status": "updated"}
