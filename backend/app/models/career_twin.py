from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    current_level = Column(Float, default=0.0)
    required_level = Column(Float, default=0.0)
    gap = Column(Float, default=0.0)
    priority = Column(Float, default=0.0)
    evidence = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


class CareerTwinSnapshot(Base):
    __tablename__ = "career_twin_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    summary = Column(Text, nullable=False)
    readiness_score = Column(Float, default=0.0)
    strong_skills = Column(String(500), nullable=True)
    weak_skills = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    candidate_profile = relationship("CandidateProfile", foreign_keys=[candidate_profile_id])


class CandidateEvent(Base):
    __tablename__ = "candidate_events"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
