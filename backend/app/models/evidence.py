from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class CandidateEvidence(Base):
    __tablename__ = "candidate_evidence"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    source_ref = Column(String(500), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    extracted_skills = Column(JSON, nullable=False, default=list)
    extracted_projects = Column(JSON, nullable=False, default=list)
    extracted_education = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=func.now())
