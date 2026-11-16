from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.skill import CandidateSkill, RoleSkill, TargetRole
from app.models.user import User
from app.services.skill_analysis import calculate_skill_gap

router = APIRouter()


def _role_view(role: TargetRole, candidate_skills: dict[int, CandidateSkill]) -> dict:
    requirements = []
    for role_skill in role.role_skills:
        candidate_skill = candidate_skills.get(role_skill.skill_id)
        current_level = float(candidate_skill.current_level if candidate_skill else 0)
        requirements.append({
            "skill_id": role_skill.skill_id,
            "skill_name": role_skill.skill.name,
            "category": role_skill.skill.category,
            "current_level": current_level,
            "required_level": role_skill.required_level,
            "gap": calculate_skill_gap(current_level, role_skill.required_level),
            "importance": role_skill.importance,
            "evidence": candidate_skill.evidence if candidate_skill else None,
            "recommended_action": f"Build evidence for {role_skill.skill.name} toward level {role_skill.required_level}.",
        })
    readiness = round(
        sum(min(r["current_level"], r["required_level"]) / r["required_level"] if r["required_level"] else 1.0 for r in requirements) / len(requirements) * 100, 1
    ) if requirements else 0.0
    total_gap = round(sum(r["gap"] for r in requirements), 1)

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "readiness_score": readiness,
        "total_gap": total_gap,
        "requirements": requirements,
    }


@router.get("")
def compare_roles(
    role_a_id: int,
    role_b_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if role_a_id == role_b_id:
        raise HTTPException(status_code=400, detail="Choose two different roles")
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    roles = db.query(TargetRole).filter(TargetRole.id.in_([role_a_id, role_b_id])).all()
    role_map = {role.id: role for role in roles}
    if len(role_map) != 2:
        raise HTTPException(status_code=404, detail="One or both roles not found")
    candidate_skills = {
        skill.skill_id: skill for skill in db.query(CandidateSkill).filter(
            CandidateSkill.candidate_profile_id == profile.id,
        ).all()
    }
    role_a_view = _role_view(role_map[role_a_id], candidate_skills)
    role_b_view = _role_view(role_map[role_b_id], candidate_skills)

    from app.services.llm_service import generate_career_comparison_explanation
    explanation = generate_career_comparison_explanation(
        candidate_name=profile.name,
        role_a_name=role_a_view["name"],
        role_a_gaps=role_a_view["requirements"],
        role_b_name=role_b_view["name"],
        role_b_gaps=role_b_view["requirements"],
    )

    return {
        "candidate": profile.name,
        "role_a": role_a_view,
        "role_b": role_b_view,
        "explanation": explanation,
    }
