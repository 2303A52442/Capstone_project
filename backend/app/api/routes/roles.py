from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.skill import CandidateTargetRole, RoleSkill, TargetRole
from app.models.user import User

router = APIRouter()


@router.get("")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(TargetRole).all()
    return [{
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "domain": role.domain,
    } for role in roles]


@router.get("/{role_id}")
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(TargetRole).filter(TargetRole.id == role_id).first()
    if not role:
        return {"detail": "Role not found"}

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "skills": [
            {
                "skill_id": rs.skill_id,
                "skill_name": rs.skill.name,
                "required_level": rs.required_level,
                "importance": rs.importance,
            }
            for rs in db.query(RoleSkill).filter(RoleSkill.role_id == role.id).all()
        ],
    }


@router.get("/current/selected")
def get_selected_target_role(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    selection = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    if not selection:
        return {"role_id": None, "role_name": None}
    return {
        "role_id": selection.role_id,
        "role_name": selection.target_role.name if selection.target_role else None,
    }


@router.put("/{role_id}/select")
def select_target_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = db.query(TargetRole).filter(TargetRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    selection = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    if selection:
        selection.role_id = role.id
    else:
        selection = CandidateTargetRole(
            candidate_profile_id=profile.id,
            role_id=role.id,
        )
        db.add(selection)

    db.flush()
    from app.services.career_twin_service import sync_career_twin_state
    sync_career_twin_state(
        db=db,
        profile=profile,
        summary=f"Target role updated to {role.name}.",
        event_type="target_role_changed",
        event_description=f"Selected target role: {role.name} ({role.domain or 'General'}).",
    )
    db.commit()
    return {"status": "selected", "role_id": role.id, "role_name": role.name}
