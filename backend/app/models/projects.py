from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(200), nullable=True)
    technologies = Column(JSON, nullable=True)
    project_link = Column(String(500), nullable=True)
    github_link = Column(String(500), nullable=True)
    role_responsibility = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    candidate_profile = relationship("CandidateProfile", back_populates="projects")
    skills = relationship("ProjectSkill", back_populates="project")


class ProjectSkill(Base):
    __tablename__ = "project_skills"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    evidence_strength = Column(Integer, default=1)

    project = relationship("Project", back_populates="skills")
