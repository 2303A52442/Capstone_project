from typing import Optional
from pydantic import BaseModel, Field


class CandidateProfileCreate(BaseModel):
    name: str
    education: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    graduation_year: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None


class CandidateProfileRead(BaseModel):
    id: int
    user_id: int
    name: str
    education: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    graduation_year: Optional[int] = None
    career_goal: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True
