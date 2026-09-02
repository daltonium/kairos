"""
backend/app/schemas/gigs.py
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GigCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    required_skill_ids: List[str] = []
    deadline: Optional[datetime] = None
    difficulty: Optional[str] = Field(default=None, pattern="^(beginner|intermediate|advanced)$")


class GigResponse(BaseModel):
    id: str
    client_id: str
    title: str
    description: Optional[str] = None
    budget: Optional[float] = None
    required_skills: Optional[str] = None
    deadline: Optional[datetime] = None
    difficulty: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class GigApplicationRequest(BaseModel):
    proposal: str = Field(min_length=1)
    price: Optional[float] = Field(default=None, ge=0)


class GigApplicationResponse(BaseModel):
    id: str
    gig_id: str
    student_id: str
    proposal: Optional[str] = None
    price: Optional[float] = None
    status: str

    class Config:
        from_attributes = True


class GigApplicationDecisionRequest(BaseModel):
    accept: bool


class GigSubmissionRequest(BaseModel):
    file_url: Optional[str] = None
    github_url: Optional[str] = None
    notes: Optional[str] = None


class GigSubmissionResponse(BaseModel):
    id: str
    application_id: str
    file_url: Optional[str] = None
    github_url: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class GigReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None
    approve: bool


class GigReviewResponse(BaseModel):
    id: str
    submission_id: str
    reviewer_type: str
    rating: Optional[int] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True
