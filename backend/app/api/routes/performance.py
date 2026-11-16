from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import get_current_user
from app.db.session import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.performance import AssessmentResult, InterviewRecord, LearningActivity, PerformanceRecord
from app.models.user import User

router = APIRouter()


@router.post("")
def add_performance(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    record_type = payload.get("record_type")
    performance = PerformanceRecord(
        candidate_profile_id=profile.id,
        record_type=record_type,
        topic=payload.get("topic"),
        score=payload.get("score"),
        difficulty=payload.get("difficulty"),
        attempts=payload.get("attempts", 1),
        notes=payload.get("notes"),
    )
    db.add(performance)
    db.commit()
    db.refresh(performance)

    if record_type == "assessment":
        db.add(AssessmentResult(
            performance_record_id=performance.id,
            total_questions=payload.get("total_questions", 0),
            correct_answers=payload.get("correct_answers", 0),
            score_percent=payload.get("score_percent", payload.get("score", 0)),
            skill_focus=payload.get("skill_focus"),
        ))
    elif record_type == "interview":
        db.add(InterviewRecord(
            performance_record_id=performance.id,
            interview_type=payload.get("interview_type"),
            technical_score=payload.get("technical_score", 0),
            communication_score=payload.get("communication_score", 0),
            problem_solving_score=payload.get("problem_solving_score", 0),
            feedback=payload.get("feedback"),
        ))
    elif record_type == "learning":
        db.add(LearningActivity(
            performance_record_id=performance.id,
            course_name=payload.get("course_name", "learning activity"),
            completion_percent=payload.get("completion_percent", 0),
            quiz_score=payload.get("quiz_score", 0),
            time_spent_hours=payload.get("time_spent_hours", 0),
        ))

    db.commit()
    return {"status": "added", "record_id": performance.id}


@router.get("")
def list_performance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db.query(PerformanceRecord).filter(PerformanceRecord.candidate_profile_id == profile.id).all()
