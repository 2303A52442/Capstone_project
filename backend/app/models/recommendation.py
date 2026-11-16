from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    target_skill = Column(String(255), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    priority = Column(Integer, default=1)
    expected_outcome = Column(Text, nullable=True)
    suggested_activity = Column(Text, nullable=True)
    estimated_effort_hours = Column(Float, default=2.0)
    success_metric = Column(Text, nullable=True)
    status = Column(String(50), default="generated")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    outcomes = relationship("RecommendationOutcome", back_populates="recommendation")


class RecommendationOutcome(Base):
    __tablename__ = "recommendation_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    accepted = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    recommendation_followed = Column(Boolean, default=False)
    before_score = Column(Float, default=0.0)
    after_score = Column(Float, default=0.0)
    improvement = Column(Float, default=0.0)
    completion_status = Column(String(50), default="pending")
    time_taken_hours = Column(Float, nullable=True)
    outcome_notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=func.now())

    recommendation = relationship("Recommendation", back_populates="outcomes")


class RecommendationExplanation(Base):
    __tablename__ = "recommendation_explanations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False, unique=True)
    explanation = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=func.now())

    recommendation = relationship("Recommendation")
