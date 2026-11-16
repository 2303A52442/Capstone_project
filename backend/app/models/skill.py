from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    candidate_skills = relationship("CandidateSkill", back_populates="skill")
    role_requirements = relationship("RoleSkill", back_populates="skill")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    current_level = Column(Float, default=0.0)
    confidence = Column(Float, default=0.5)
    evidence = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    candidate_profile = relationship("CandidateProfile", back_populates="skills")
    skill = relationship("Skill", back_populates="candidate_skills")


class TargetRole(Base):
    __tablename__ = "target_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    role_skills = relationship("RoleSkill", back_populates="target_role")
    candidate_targets = relationship("CandidateTargetRole", back_populates="target_role")


class RoleSkill(Base):
    __tablename__ = "role_skills"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("target_roles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    required_level = Column(Float, default=0.0)
    importance = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)

    target_role = relationship("TargetRole", back_populates="role_skills")
    skill = relationship("Skill", back_populates="role_requirements")


class CandidateTargetRole(Base):
    __tablename__ = "candidate_target_roles"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("target_roles.id"), nullable=False)

    candidate_profile = relationship("CandidateProfile", back_populates="target_roles")
    target_role = relationship("TargetRole", back_populates="candidate_targets")
