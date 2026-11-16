import re

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.evidence import CandidateEvidence
from app.models.projects import Project
from app.models.skill import CandidateSkill, Skill
from app.models.user import User
from app.services.evidence_analysis import analyze_text, extract_resume_text

router = APIRouter()


def _profile(current_user: User, db: Session) -> CandidateProfile:
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


def _view(item: CandidateEvidence) -> dict:
    return {"id": item.id, "source": item.source, "source_ref": item.source_ref, "title": item.title,
            "extracted_skills": item.extracted_skills or [], "extracted_projects": item.extracted_projects or [],
            "extracted_education": item.extracted_education or [], "status": item.status, "created_at": item.created_at}


@router.get("")
def list_evidence(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _profile(current_user, db)
    return [_view(item) for item in db.query(CandidateEvidence).filter(CandidateEvidence.candidate_profile_id == profile.id).order_by(CandidateEvidence.created_at.desc()).all()]


@router.post("/resume/analyze")
async def analyze_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Upload a PDF resume")
    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume must be 5 MB or smaller")
    try:
        text = extract_resume_text(file_bytes)
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Resume parsing failed: {error}") from error
    profile = _profile(current_user, db)
    result = analyze_text(text, db.query(Skill).all(), "Resume", file.filename or "resume.pdf")
    item = CandidateEvidence(candidate_profile_id=profile.id, **result)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _view(item)


@router.post("/github/analyze")
def analyze_github(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    username = str(payload.get("username", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        raise HTTPException(status_code=400, detail="Enter a valid GitHub username")
    try:
        response = httpx.get(f"https://api.github.com/users/{username}/repos", params={"per_page": 100, "type": "owner"}, headers={"Accept": "application/vnd.github+json"}, timeout=10)
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail="GitHub could not be reached") from error
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="GitHub user not found")
    if response.status_code == 403:
        raise HTTPException(status_code=429, detail="GitHub rate limit reached; try again later")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub returned an error")
    repositories = response.json()
    text = "\n".join(f"{repo.get('name', '')}: {repo.get('description') or ''}; languages: {', '.join((repo.get('language') or '',))}" for repo in repositories)
    profile = _profile(current_user, db)
    result = analyze_text(text, db.query(Skill).all(), "GitHub", username, f"https://github.com/{username}")
    result["extracted_projects"] = [{"name": repo.get("name"), "description": repo.get("description"), "github_link": repo.get("html_url"), "technologies": [repo.get("language")] if repo.get("language") else []} for repo in repositories if repo.get("name")]
    item = CandidateEvidence(candidate_profile_id=profile.id, **result)
    db.add(item)
    db.commit()
    db.refresh(item)
    return _view(item)


@router.post("/{evidence_id}/confirm")
def confirm_evidence(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _profile(current_user, db)
    item = db.query(CandidateEvidence).filter(CandidateEvidence.id == evidence_id, CandidateEvidence.candidate_profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="Evidence has already been reviewed")
    for extracted in item.extracted_skills or []:
        skill = db.query(Skill).filter(Skill.id == extracted["skill_id"]).first()
        if not skill:
            continue
        candidate_skill = db.query(CandidateSkill).filter(CandidateSkill.candidate_profile_id == profile.id, CandidateSkill.skill_id == skill.id).first()
        source_note = f"{item.source}: {item.source_ref or item.title}"
        if candidate_skill:
            candidate_skill.evidence = f"{candidate_skill.evidence or ''} {source_note}".strip()
            candidate_skill.confidence = max(float(candidate_skill.confidence or 0), 0.6 if item.source == "Resume" else 0.5)
        else:
            db.add(CandidateSkill(candidate_profile_id=profile.id, skill_id=skill.id, current_level=0, confidence=0.6 if item.source == "Resume" else 0.5, evidence=source_note))
    for project in item.extracted_projects or []:
        if project.get("name") and not db.query(Project).filter(Project.candidate_profile_id == profile.id, Project.name == project["name"]).first():
            db.add(Project(candidate_profile_id=profile.id, name=project["name"], description=project.get("description"), technologies=project.get("technologies"), github_link=project.get("github_link")))
    item.status = "confirmed"
    from app.services.career_twin_service import sync_career_twin_state
    sync_career_twin_state(
        db=db,
        profile=profile,
        summary=f"Confirmed {item.source} evidence: {item.title}.",
        event_type="evidence_confirmed",
        event_description=f"Confirmed {item.source} evidence ({item.title}) with {len(item.extracted_skills or [])} skill(s).",
    )
    db.commit()
    return {"status": "confirmed", "evidence_id": item.id}


@router.post("/{evidence_id}/reject")
def reject_evidence(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _profile(current_user, db)
    item = db.query(CandidateEvidence).filter(CandidateEvidence.id == evidence_id, CandidateEvidence.candidate_profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Evidence not found")
    item.status = "rejected"
    db.commit()
    return {"status": "rejected", "evidence_id": item.id}