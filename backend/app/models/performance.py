from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(Integer, primary_key=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    topic = Column(String(255), nullable=True)
    score = Column(Float, nullable=True)
    difficulty = Column(String(50), nullable=True)
    attempts = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=func.now())

    candidate_profile = relationship("CandidateProfile", back_populates="performances")
    assessment_data = relationship("AssessmentResult", back_populates="performance_record", uselist=False)
    interview_data = relationship("InterviewRecord", back_populates="performance_record", uselist=False)
    learning_data = relationship("LearningActivity", back_populates="performance_record", uselist=False)


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    performance_record_id = Column(Integer, ForeignKey("performance_records.id"), nullable=False)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score_percent = Column(Float, default=0.0)
    skill_focus = Column(String(255), nullable=True)

    performance_record = relationship("PerformanceRecord", back_populates="assessment_data")


class InterviewRecord(Base):
    __tablename__ = "interview_records"

    id = Column(Integer, primary_key=True, index=True)
    performance_record_id = Column(Integer, ForeignKey("performance_records.id"), nullable=False)
    interview_type = Column(String(100), nullable=True)
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    problem_solving_score = Column(Float, default=0.0)
    feedback = Column(Text, nullable=True)

    performance_record = relationship("PerformanceRecord", back_populates="interview_data")


class LearningActivity(Base):
    __tablename__ = "learning_activities"

    id = Column(Integer, primary_key=True, index=True)
    performance_record_id = Column(Integer, ForeignKey("performance_records.id"), nullable=False)
    course_name = Column(String(255), nullable=False)
    completion_percent = Column(Float, default=0.0)
    quiz_score = Column(Float, default=0.0)
    time_spent_hours = Column(Float, default=0.0)

    performance_record = relationship("PerformanceRecord", back_populates="learning_data")
