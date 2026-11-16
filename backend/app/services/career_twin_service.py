from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.career_twin import CareerTwinSnapshot, CandidateEvent, SkillGap
from app.models.skill import CandidateSkill, CandidateTargetRole, RoleSkill
from app.services.skill_analysis import calculate_skill_gap, rank_skill_gaps


def _score_to_percent(score: float) -> float:
    value = float(score or 0)
    return value * 20 if 0 <= value <= 5 else value


def calculate_skill_improvement(before_score: float, after_score: float) -> float:
    """Convert assessment improvement into the deterministic 0-5 skill scale."""
    before_percent = _score_to_percent(before_score)
    after_percent = _score_to_percent(after_score)
    return round((after_percent - before_percent) / 100 * 5, 2)


def sync_career_twin_state(
    db: Session,
    profile: CandidateProfile,
    summary: str | None = None,
    event_type: str = "state_synchronized",
    event_description: str | None = None,
) -> dict:
    """Synchronize candidate skill gaps, readiness score, Career Twin snapshot, and timeline event."""
    target = db.query(CandidateTargetRole).filter(
        CandidateTargetRole.candidate_profile_id == profile.id,
    ).first()
    role_skills = db.query(RoleSkill).filter(RoleSkill.role_id == target.role_id).all() if target else []
    candidate_skills = {
        skill.skill_id: skill for skill in db.query(CandidateSkill).filter(
            CandidateSkill.candidate_profile_id == profile.id,
        ).all()
    }

    gaps = []
    for role_skill in role_skills:
        current = candidate_skills.get(role_skill.skill_id)
        current_level = float(current.current_level if current else 0)
        gaps.append({
            "skill_name": role_skill.skill.name,
            "current_level": current_level,
            "required_level": float(role_skill.required_level),
            "gap": calculate_skill_gap(current_level, role_skill.required_level),
            "importance": float(role_skill.importance),
            "confidence": float(current.confidence if current else 0),
            "recency": 1.0 if current else 0,
            "evidence": current.evidence if current else "No evidence recorded",
        })

    ranked_gaps = rank_skill_gaps(gaps)
    db.query(SkillGap).filter(SkillGap.candidate_profile_id == profile.id).delete()
    for gap in ranked_gaps:
        db.add(SkillGap(
            candidate_profile_id=profile.id,
            skill_name=gap["skill_name"],
            current_level=gap["current_level"],
            required_level=gap["required_level"],
            gap=gap["gap"],
            priority=gap["priority_score"],
            evidence=gap["evidence"],
        ))

    readiness = 0.0
    if role_skills:
        readiness = sum(
            min(candidate_skills.get(item.skill_id).current_level if candidate_skills.get(item.skill_id) else 0, item.required_level) / item.required_level
            if item.required_level else 1
            for item in role_skills
        ) / len(role_skills)
    strong_skills = [item.skill.name for item in candidate_skills.values() if item.current_level >= 3.5]
    weak_skills = [gap["skill_name"] for gap in ranked_gaps if gap["gap"] > 0]

    snapshot_summary = summary or f"Career Twin state synchronized for {profile.name}."
    db.add(CareerTwinSnapshot(
        candidate_profile_id=profile.id,
        summary=snapshot_summary,
        readiness_score=round(readiness * 100, 2),
        strong_skills=", ".join(strong_skills),
        weak_skills=", ".join(weak_skills),
    ))
    db.add(CandidateEvent(
        candidate_profile_id=profile.id,
        event_type=event_type,
        description=event_description or snapshot_summary,
    ))
    db.flush()
    return {
        "readiness_score": round(readiness * 100, 2),
        "strong_skills": strong_skills,
        "weak_skills": weak_skills,
        "skill_gaps": ranked_gaps,
    }


def refresh_candidate_state(
    db: Session,
    profile: CandidateProfile,
    target_skill: str,
    before_score: float,
    after_score: float,
    outcome_notes: str | None = None,
) -> dict:
    """Apply an outcome and rebuild persisted gaps and Career Twin history."""
    candidate_skill = db.query(CandidateSkill).join(CandidateSkill.skill).filter(
        CandidateSkill.candidate_profile_id == profile.id,
        CandidateSkill.skill.has(name=target_skill),
    ).first()
    if not candidate_skill:
        raise ValueError(f"Candidate skill not found: {target_skill}")

    previous_level = round(float(candidate_skill.current_level or 0), 2)
    improvement = calculate_skill_improvement(before_score, after_score)
    candidate_skill.current_level = round(min(5.0, max(0.0, previous_level + improvement)), 2)
    candidate_skill.evidence = (
        f"{candidate_skill.evidence or 'No prior evidence'}. "
        f"Outcome update: {previous_level} -> {candidate_skill.current_level}. "
        f"{outcome_notes or 'Improved performance evidence.'}"
    )

    sync_result = sync_career_twin_state(
        db=db,
        profile=profile,
        summary=f"Updated after {target_skill} outcome: skill level {previous_level} -> {candidate_skill.current_level}.",
        event_type="skill_outcome_applied",
        event_description=f"{target_skill} changed from {previous_level} to {candidate_skill.current_level}.",
    )

    return {
        "skill_name": target_skill,
        "previous_level": previous_level,
        "current_level": candidate_skill.current_level,
        "improvement": improvement,
        "skill_gaps": sync_result["skill_gaps"],
        "readiness_score": sync_result["readiness_score"],
    }

