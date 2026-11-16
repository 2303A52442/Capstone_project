from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    education = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    career_goal = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="candidate_profile")
    target_roles = relationship("CandidateTargetRole", back_populates="candidate_profile")
    skills = relationship("CandidateSkill", back_populates="candidate_profile")
    projects = relationship("Project", back_populates="candidate_profile")
    performances = relationship("PerformanceRecord", back_populates="candidate_profile")
