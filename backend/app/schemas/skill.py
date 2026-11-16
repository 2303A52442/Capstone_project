from typing import Optional
from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


class SkillRead(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CandidateSkillUpdate(BaseModel):
    skill_id: int
    current_level: float
    confidence: float = 0.5
    evidence: Optional[str] = None
