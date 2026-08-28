"""
backend/app/schemas/roadmap.py
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class RoadmapGenerateRequest(BaseModel):
    interest: str = Field(min_length=1, max_length=100)
    skill_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    career_goal: Optional[str] = None
    weeks: int = Field(default=12, ge=1, le=52)


class RoadmapItemResponse(BaseModel):
    id: str
    week_number: int
    title: str
    description: Optional[str] = None
    estimated_hours: Optional[int] = None
    difficulty: Optional[str] = None
    is_completed: bool

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: str
    interest: str
    skill_level: str
    career_goal: Optional[str] = None
    status: str
    items: List[RoadmapItemResponse] = []

    class Config:
        from_attributes = True


class RoadmapGenerateAcceptedResponse(BaseModel):
    roadmap_id: str
    status: str
