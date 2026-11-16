from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RecommendationCreate(BaseModel):
    target_skill: str
    recommendation_text: str
    reason: Optional[str] = None
    priority: int = 1
    expected_outcome: Optional[str] = None
    suggested_activity: Optional[str] = None
    estimated_effort_hours: float = 2.0
    success_metric: Optional[str] = None


class RecommendationRead(BaseModel):
    id: int
    candidate_profile_id: int
    target_skill: str
    recommendation_text: str
    reason: Optional[str] = None
    priority: int
    expected_outcome: Optional[str] = None
    suggested_activity: Optional[str] = None
    estimated_effort_hours: float
    success_metric: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendationExplanationRead(BaseModel):
    id: int
    recommendation_id: int
    explanation: str
    generated_at: datetime

    class Config:
        from_attributes = True
